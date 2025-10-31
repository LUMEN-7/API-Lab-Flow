# crud_basico.py

from datetime import datetime, date
from flask import request, jsonify
from core.database import get_connection
from psycopg2 import sql, DatabaseError
from psycopg2.extras import RealDictCursor # Importante para get_item
from psycopg2.errors import UndefinedTable, SyntaxError, OperationalError
import bcrypt
import math

# ===========================================================================
# == 1. FUNÇÕES AUXILIARES (HELPERS)
# ===========================================================================

# --- Helpers de Propósito Geral (Dados) ---

def parse_data_segura(valor):
    """(Sem alteração) Tenta converter uma string em um objeto date."""
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str):
        return valor

    formatos_validos = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    for formato in formatos_validos:
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    return valor

def _convert_to_numeric(value_str: str):
    """(Helper) Tenta converter um valor string para float."""
    if value_str is None:
        raise ValueError("Valor não pode ser nulo para operador numérico")
    try:
        return float(value_str)
    except (ValueError, TypeError):
        raise ValueError(f"Valor '{value_str}' não é um número válido.")

def _format_and_filter_row(row_dict: dict, campos_nao_permitidos: set) -> dict:
    """
    (Helper) Processa um único dicionário de resultado.
    Remove campos proibidos e formata datas para JSON (isoformat).
    """
    item = {}
    if not row_dict:
        return item
    
    for key, val in row_dict.items():
        if key in campos_nao_permitidos:
            continue
        if isinstance(val, (datetime, date)):
            item[key] = val.isoformat()
        else:
            item[key] = val
    return item

def _process_result_rows(rows: list, campos_nao_permitidos: set) -> list:
    """(Helper) Aplica a formatação e filtro em uma lista de resultados."""
    return [_format_and_filter_row(row, campos_nao_permitidos) for row in rows]

# --- Helpers de Construção de Query (Query Builders) ---

def _build_dynamic_where_clause(args: dict, colunas_validas: set) -> (list, list):
    """
    (Helper) Constrói a cláusula WHERE dinâmica a partir dos request.args.
    Retorna a lista de cláusulas SQL e a lista de parâmetros.
    """
    params = []
    where_clauses = [sql.SQL("1=1")]
    
    for key, value in args.items():
        if key in ['page', 'itens_por_pagina']:
            continue

        parts = key.split('__')
        field_name = parts[0]
        operator = 'exact' if len(parts) == 1 else parts[1]

        if field_name not in colunas_validas:
            raise ValueError(f"Coluna inválida para filtro: {field_name}")
        
        col = sql.Identifier(field_name)

        match operator:
            case 'exact':
                where_clauses.append(sql.SQL("{c} = %s").format(c=col))
                params.append(value)
            case 'in':
                values_list = tuple(value.split(','))
                where_clauses.append(sql.SQL("{c} IN %s").format(c=col))
                params.append(values_list)
            case 'ilike':
                where_clauses.append(sql.SQL("{c} ILIKE %s").format(c=col))
                params.append(f"%{value}%")
            case 'gt':
                where_clauses.append(sql.SQL("{c} > %s").format(c=col))
                params.append(_convert_to_numeric(value))
            case 'gte':
                where_clauses.append(sql.SQL("{c} >= %s").format(c=col))
                params.append(_convert_to_numeric(value))
            case 'lt':
                where_clauses.append(sql.SQL("{c} < %s").format(c=col))
                params.append(_convert_to_numeric(value))
            case 'lte':
                where_clauses.append(sql.SQL("{c} <= %s").format(c=col))
                params.append(_convert_to_numeric(value))
            case 'date':
                where_clauses.append(sql.SQL("DATE({c}) = %s").format(c=col))
                params.append(value)
    
    return where_clauses, params

def _build_insert_query(tabela, colunas, coluna_retorno):
    """(Helper) Constrói a query SQL de INSERT segura."""
    return sql.SQL("INSERT INTO {tabela} ({colunas}) VALUES ({valores}) RETURNING {coluna_retorno}").format(
        tabela=sql.Identifier(tabela),
        colunas=sql.SQL(', ').join(map(sql.Identifier, colunas)),
        valores=sql.SQL(', ').join(sql.Placeholder() * len(colunas)),
        coluna_retorno=sql.Identifier(coluna_retorno)
    )

def _build_update_set_clause(data_convertida: dict, campos_permitidos: list) -> (list, list):
    """
    (Helper) Constrói a cláusula SET para um UPDATE.
    Lida com a lógica de hash de senha.
    """
    colunas_sql = []
    valores = []
    
    for campo in campos_permitidos:
        if campo in data_convertida and data_convertida[campo] is not None:
            # Lógica de negócio específica (ex: hash de senha)
            if campo == "senha_user":
                senha_hash = bcrypt.hashpw(data_convertida[campo].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                colunas_sql.append(sql.SQL("{} = %s").format(sql.Identifier(campo)))
                valores.append(senha_hash)
            else:
                colunas_sql.append(sql.SQL("{} = %s").format(sql.Identifier(campo)))
                valores.append(data_convertida[campo])
                
    return colunas_sql, valores

# --- Helpers de Paginação e Execução ---

def _parse_pagination_args(args: dict) -> (int, int, int):
    """(Helper) Valida e retorna (limite, offset, pagina_atual)."""
    try:
        pagina = int(args.get("page", 1))
        itens_por_pagina = int(args.get("itens_por_pagina", 10))
        if pagina < 1 or itens_por_pagina < 1:
            raise ValueError("Parâmetros de página não podem ser menores que 1")
        offset = (pagina - 1) * itens_por_pagina
        return itens_por_pagina, offset, pagina
    except ValueError as e:
        raise ValueError(f"Parâmetros de página inválidos: {e}")

def _execute_count_query(cur, tabela, where_clause_sql, params) -> int:
    """(Helper) Executa a query de contagem total de itens."""
    count_query = sql.SQL("SELECT COUNT(*) AS total FROM {t} WHERE {w}").format(
        t=sql.Identifier(tabela),
        w=where_clause_sql
    )
    cur.execute(count_query, tuple(params))
    resultado = cur.fetchone()
    return resultado["total"] if resultado else 0

def _build_metadata_dict(pagina, itens_por_pagina, total_items) -> dict:
    """(Helper) Monta o dicionário de metadados para a paginação."""
    return {
        "pagina": pagina,
        "itens_por_pagina": itens_por_pagina,
        "total_items": total_items,
        "total_pages": math.ceil(total_items / itens_por_pagina) if total_items > 0 else 1
    }

def _execute_data_query(cur, tabela, where_clause_sql, order_by, limit, offset, params):
    """(Helper) Executa a query principal que busca os dados paginados."""
    data_query = sql.SQL("SELECT * FROM {t} WHERE {w} ORDER BY {o} LIMIT %s OFFSET %s").format(
        t=sql.Identifier(tabela),
        w=where_clause_sql,
        o=sql.Identifier(order_by)
    )
    params_paginada = params + [limit, offset]
    cur.execute(data_query, tuple(params_paginada))
    return cur.fetchall()


# ===========================================================================
# == 2. FUNÇÕES PÚBLICAS (CRUD)
# ===========================================================================

def inserir_elemento_generico(tabela, data, coluna_retorno="id"):
    """
    (Pública) Insere um novo elemento genérico no banco de dados.
    Orquestra a validação, conversão de dados, construção da query e execução.
    """
    try:
        if not tabela or not isinstance(tabela, str) or not data or not isinstance(data, dict):
            return jsonify({"erro": "Nome da tabela ou dados inválidos"}), 400

        conn = get_connection()
        cur = conn.cursor()

        # 1. Transformação de Dados
        data_convertida = {k: parse_data_segura(v) for k, v in data.items()}
        if not data_convertida:
            return jsonify({"erro": "Nenhum dado válido encontrado"}), 400
        
        colunas = list(data_convertida.keys())
        valores = list(data_convertida.values())

        # 2. Construção da Query (usando helper)
        query = _build_insert_query(tabela, colunas, coluna_retorno)
        print(valores)
        # 3. Execução
        cur.execute(query, valores)
        new_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"sucesso": True, "id_inserido": new_id}), 200

    except (UndefinedTable, SyntaxError, DatabaseError) as e:
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"erro": f"Não foi possível colocar a nova entrada: {str(e)}"}), 400


def lista_itens(tabela, colunas_validas, default_order_by, campos_nao_permitidos=None):
    """
    (Pública) Orquestra a listagem, filtragem e paginação de itens.
    Chama helpers para parsear paginação, construir WHERE, executar queries e formatar.
    """
    if campos_nao_permitidos is None:
        campos_nao_permitidos = set()
    
    conn = None # Garantir que conn exista no finally
    try:
        # 1. Parse de Paginação
        limit, offset, pagina_atual = _parse_pagination_args(request.args)
        
        # 2. Construção da Cláusula WHERE
        
        where_clauses, params = _build_dynamic_where_clause(request.args, colunas_validas)
        where_sql = sql.SQL(" AND ").join(where_clauses)

        # 3. Conexão e Execução das Queries
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 3a. Query de Contagem
        total_items = _execute_count_query(cur, tabela, where_sql, params)
        
        # 3b. Query de Dados
        rows = _execute_data_query(cur, tabela, where_sql, default_order_by, limit, offset, params)

        # 4. Processamento e Formatação
        data = _process_result_rows(rows, campos_nao_permitidos)
        metadata = _build_metadata_dict(pagina_atual, limit, total_items)
        
        return jsonify({"data": data, "metadata": metadata}), 200

    except ValueError as e: # Captura erros de _parse_pagination_args e _build_dynamic_where_clause
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro em lista_itens({tabela}): {e}")
        return jsonify({"erro": "Erro interno ao listar itens"}), 500
    finally:
        if conn:
            conn.close()


def get_item(tabela, id_base, id_busca, campos_nao_permitidos=None):
    """
    (Pública) Busca um item específico.
    Refatorado para usar RealDictCursor (1 query) e o helper de formatação.
    """
    if campos_nao_permitidos is None:
        campos_nao_permitidos = set()
        
    try:
        if not all([tabela, id_base, id_busca]) or not isinstance(tabela, str) or not isinstance(id_base, str):
            return jsonify({"erro": "Parâmetros inválidos"}), 400

        conn = get_connection()
        # Usar RealDictCursor para obter um dicionário diretamente
        cur = conn.cursor(cursor_factory=RealDictCursor) 

        # Simplificado para 1 query
        query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
            sql.Identifier(tabela),
            sql.Identifier(id_base)
        )

        cur.execute(query, (id_busca,))
        row_dict = cur.fetchone()

        if not row_dict:
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404

        # 2. Reutiliza o helper de formatação e filtro
        data = _format_and_filter_row(row_dict, campos_nao_permitidos)

        cur.close()
        conn.close()

        return jsonify(data), 200

    except (OperationalError, DatabaseError) as e:
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400


def deletar_item(tabela, id_base, id_busca):
    """
    (Pública) Deleta um item.
    (Sem alteração - Função já era simples e com responsabilidade única)
    """
    try:
        if not all([tabela, id_base, id_busca]) or not isinstance(tabela, str) or not isinstance(id_base, str):
            return jsonify({"erro": "Parâmetros inválidos"}), 400

        conn = get_connection()
        cur = conn.cursor()

        query = sql.SQL("DELETE FROM {} WHERE {} = %s RETURNING *").format(
            sql.Identifier(tabela),
            sql.Identifier(id_base)
        )

        cur.execute(query, (id_busca,))
        deleted = cur.fetchone()

        if not deleted:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"mensagem": "Item deletado com sucesso!"}), 200

    except (OperationalError, DatabaseError) as e:
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400


def atualizar_itens(tabela, campos_permitidos, id_base, id_busca, data):
    """
    (Pública) Orquestra a atualização de um item.
    Chama helpers para converter dados e construir a cláusula SET.
    """
    try:
        if not all([tabela, id_base, id_busca, campos_permitidos, data]):
            return jsonify({"erro": "Parâmetros inválidos"}), 400
        
        conn = get_connection()
        cur = conn.cursor()

        # 1. Transformação de Dados
        data_convertida = {k: parse_data_segura(v) for k, v in data.items()}

        # 2. Construção da Cláusula SET (usando helper)
        colunas_sql, valores = _build_update_set_clause(data_convertida, campos_permitidos)

        if not colunas_sql:
            return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

        # 3. Construção da Query Final
        query = sql.SQL("UPDATE {tabela} SET {set_clause} WHERE {id_coluna} = %s RETURNING *").format(
            tabela=sql.Identifier(tabela),
            set_clause=sql.SQL(", ").join(colunas_sql),
            id_coluna=sql.Identifier(id_base)
        )
        valores.append(id_busca) # Adiciona o valor do WHERE

        # 4. Execução
        cur.execute(query, tuple(valores))
        updated = cur.fetchone()

        if not updated:
            conn.rollback()
            return jsonify({"erro": "Item não encontrado"}), 404

        conn.commit()
        
        # Formata o retorno para ser um dict (como no get_item)
        colunas_retorno = [desc[0] for desc in cur.description]
        data_retorno = dict(zip(colunas_retorno, updated))
        
        # Reutiliza o helper para limpar e formatar a resposta
        data_limpa = _format_and_filter_row(data_retorno, set()) # Não remove nada

        cur.close()
        conn.close()

        return jsonify({
            "mensagem": "Item atualizado com sucesso!",
            "item_atualizado": data_limpa
        }), 200

    except (OperationalError, DatabaseError) as e:
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400