from datetime import datetime, date
from flask import request, jsonify
from core.database import get_connection
from psycopg2 import sql, DatabaseError
from psycopg2.extras import RealDictCursor # Crucial para dicts
from psycopg2.errors import UndefinedTable, SyntaxError, OperationalError
import bcrypt
import math



def parse_data_segura(valor):
    """Tenta converter uma string em um objeto date. Retorna o valor original se não for data."""
    if isinstance(valor, date):
        return valor  # já é um date
    if not isinstance(valor, str):
        return valor  # não é string, retorna como está

    formatos_validos = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    for formato in formatos_validos:
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    return valor  # retorna original se não for data válida


def inserir_elemento_generico(tabela, data, coluna_retorno="id"):
    try:
            
            # Verificações básicas
            if not tabela or not isinstance(tabela, str):
                return jsonify({"erro": "Nome da tabela inválido"}), 400
            
            if not data or not isinstance(data, dict):
                return jsonify({"erro": "Dados inválidos para inserção"}), 400

            # Conexão com o banco
            conn = get_connection()
            cur = conn.cursor()

            # Converter possíveis datas antes de inserir
            data_convertida = {k: parse_data_segura(v) for k, v in data.items()}

            # Verificar se há colunas e valores válidos
            if not data_convertida:
                return jsonify({"erro": "Nenhum dado válido encontrado"}), 400

            colunas = list(data_convertida.keys())
            valores = list(data_convertida.values())

            # Construir SQL com segurança
            query = sql.SQL("INSERT INTO {tabela} ({colunas}) VALUES ({valores}) RETURNING {coluna_retorno}").format(
                tabela=sql.Identifier(tabela),
                colunas=sql.SQL(', ').join(map(sql.Identifier, colunas)),
                valores=sql.SQL(', ').join(sql.Placeholder() * len(colunas)),
                coluna_retorno=sql.Identifier(coluna_retorno)
            )

            cur.execute(query, valores)
            new_id = cur.fetchone()[0]

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"sucesso": True, "id_inserido": new_id}), 200

    except UndefinedTable:
        return jsonify({"erro": f"Tabela '{tabela}' não existe"}), 400
    
    except SyntaxError:
        return jsonify({"erro": "Erro de sintaxe SQL"}), 400

    except DatabaseError as e:
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"erro": f"Não foi possível colocar a nova entrada: {str(e)}"}), 400


def lista_itens(tabela, colunas_validas, default_order_by, campos_nao_permitidos=None):
    """
    Função genérica para listar, filtrar (genericamente) e paginar itens.
    Retorna no formato padronizado {"data": [...], "metadata": {...}}.
    
    :param tabela: Nome da tabela no banco (ex: "pedido").
    :param colunas_validas: Um set de strings com nomes de colunas que são
                            permitidas para filtragem (ex: {"n_pedido", "status"}).
                            Também usado para segurança de 'default_order_by'.
    :param default_order_by: A coluna para ordenação padrão (ex: "n_pedido").
    :param campos_nao_permitidos: Um set de colunas para excluir da resposta
                                  (ex: {"senha_user"}).
    """
    if campos_nao_permitidos is None:
        campos_nao_permitidos = set()
    
    if default_order_by not in colunas_validas and not default_order_by.startswith("id_"):
         # Permite IDs por padrão, mesmo que não listados
         # Mas idealmente, 'default_order_by' deve estar em 'colunas_validas'
         pass # Em um cenário real, você poderia lançar um erro aqui

    # --- 1. Obter Parâmetros de Query ---
    filtro_coluna = request.args.get("coluna")
    filtro_valor = request.args.get("valor")
    
    try:
        # Padrões: Página 1, 10 itens por página
        pagina = int(request.args.get("pagina", 1))
        itens_por_pagina = int(request.args.get("itens_por_pagina", 10))
        if pagina < 1 or itens_por_pagina < 1:
            raise ValueError
    except ValueError:
        return jsonify({"erro": "Parâmetros de página inválidos"}), 400

    offset = (pagina - 1) * itens_por_pagina

    # --- 2. Construir Cláusula WHERE Dinâmica ---
    params = []
    # Começa com uma condição verdadeira para facilitar a adição de ANDs
    where_clauses = [sql.SQL("1=1")] 

    if filtro_coluna and filtro_valor:
        if filtro_coluna not in colunas_validas:
            return jsonify({"erro": f"Coluna inválida para filtro: {filtro_coluna}"}), 400
        
        # Tratamento especial para datas (como no seu base.py)
        if "data" in filtro_coluna:
             where_clauses.append(sql.SQL("DATE({col}) = %s").format(col=sql.Identifier(filtro_coluna)))
        else:
             where_clauses.append(sql.SQL("{col} = %s").format(col=sql.Identifier(filtro_coluna)))
        params.append(filtro_valor)

    # --- 3. Conexão e Execução das Queries ---
    conn = get_connection()
    # Use RealDictCursor para obter resultados como dicionários automaticamente
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # --- Query 1: Contagem Total (para metadados) ---
        count_query_sql = sql.SQL("SELECT COUNT(*) AS total FROM {t} WHERE {w}").format(
            t=sql.Identifier(tabela),
            w=sql.SQL(" AND ").join(where_clauses)
        )
        
        cur.execute(count_query_sql, tuple(params))
        resultado_contagem = cur.fetchone()
        total_items = resultado_contagem["total"] if resultado_contagem else 0
        
        total_pages = math.ceil(total_items / itens_por_pagina) if total_items > 0 else 1

        # --- Query 2: Dados Paginados ---
        data_query_sql = sql.SQL("SELECT * FROM {t} WHERE {w} ORDER BY {o} LIMIT %s OFFSET %s").format(
            t=sql.Identifier(tabela),
            w=sql.SQL(" AND ").join(where_clauses),
            o=sql.Identifier(default_order_by) # Ordenação
        )
        
        # Adiciona os parâmetros de paginação (LIMIT e OFFSET)
        params_paginada = params + [itens_por_pagina, offset]
        
        cur.execute(data_query_sql, tuple(params_paginada))
        rows = cur.fetchall() # rows já serão uma lista de dicts
        
        # --- 4. Processar Resultados ---
        data = []
        for row_dict in rows:
            item = {}
            for key, val in row_dict.items():
                # Pula colunas que não queremos expor (ex: senha)
                if key in campos_nao_permitidos:
                    continue
                
                if isinstance(val, datetime):
                    # Força a formatação para 'AAAA-MM-DD'
                    item[key] = val.strftime('%Y-%m-%d')
                
                # Se for um objeto date (sem hora)
                elif isinstance(val, date):
                    # O isoformat() já retorna 'AAAA-MM-DD'
                    item[key] = val.isoformat()
                else:
                    # Deixa os outros valores (int, string, bool) como estão
                    item[key] = val
                
            data.append(item)

        # --- 5. Montar Resposta Padronizada ---
        metadata = {
            "pagina": pagina,
            "itens_por_pagina": itens_por_pagina,
            "total_items": total_items,
            "total_pages": total_pages
        }
        # print({"data": data, "metadata": metadata})
        return jsonify({"data": data, "metadata": metadata}), 200

    except Exception as e:
        conn.rollback()
        print(f"Erro em lista_itens({tabela}): {e}") # Log de erro no console
        return jsonify({"erro": "Erro interno ao listar itens"}), 500
    finally:
        cur.close()
        conn.close()

    
def get_item(tabela, id_base, id_busca, campos_nao_permitidos=None):
    try:
        # Verificações básicas
        if not all([tabela, id_base, id_busca]):
            return jsonify({"erro": "Parâmetros inválidos"}), 400

        if not isinstance(tabela, str) or not isinstance(id_base, str):
            return jsonify({"erro": "Nome da tabela ou coluna inválido"}), 400

        conn = get_connection()
        cur = conn.cursor()

        query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
            sql.Identifier(tabela),
            sql.Identifier(id_base)
        )

        cur.execute(query, (id_busca,))
        todas_colunas = [desc[0] for desc in cur.description]

        if campos_nao_permitidos:
            colunas_filtradas = [col for col in todas_colunas if col not in campos_nao_permitidos]
        else:
            colunas_filtradas = todas_colunas

        # Consulta segura — previne SQL injection
        query = sql.SQL("SELECT {} FROM {} WHERE {} = %s").format(
            sql.SQL(", ").join(map(sql.Identifier, colunas_filtradas)),
            sql.Identifier(tabela),
            sql.Identifier(id_base)
        )

        cur.execute(query, (id_busca,))
        row = cur.fetchone()

        # Se não encontrar resultado
        if not row:
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404

        colunas = [desc[0] for desc in cur.description]
        data = dict(zip(colunas, row))

        cur.close()
        conn.close()

        return jsonify(data), 200

    except OperationalError:
        return jsonify({"erro": "Erro na conexão com o banco de dados"}), 500

    except DatabaseError as e:
        return jsonify({"erro": f"Erro ao buscar item: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400


def deletar_item(tabela, id_base, id_busca):
    try:
        #  Verificações básicas
        if not all([tabela, id_base, id_busca]):
            return jsonify({"erro": "Parâmetros inválidos"}), 400

        if not isinstance(tabela, str) or not isinstance(id_base, str):
            return jsonify({"erro": "Nome da tabela ou coluna inválido"}), 400

        conn = get_connection()
        cur = conn.cursor()

        #  Query segura contra SQL Injection
        query = sql.SQL("DELETE FROM {} WHERE {} = %s RETURNING *").format(
            sql.Identifier(tabela),
            sql.Identifier(id_base)
        )

        cur.execute(query, (id_busca,))
        deleted = cur.fetchone()

        # Se não deletou nada
        if not deleted:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"mensagem": "Item deletado com sucesso!"}), 200

    except OperationalError:
        return jsonify({"erro": "Erro na conexão com o banco de dados"}), 500

    except DatabaseError as e:
        return jsonify({"erro": f"Erro ao deletar item: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400


def atualizar_itens(tabela, campos_permitidos, id_base, id_busca, data):
    try:
        # ⚙️ Validações iniciais
        if not all([tabela, id_base, id_busca, campos_permitidos, data]):
            return jsonify({"erro": "Parâmetros inválidos"}), 400
        
        if not isinstance(tabela, str) or not isinstance(id_base, str):
            return jsonify({"erro": "Nome da tabela ou coluna inválido"}), 400

        if not isinstance(campos_permitidos, (list, tuple)):
            return jsonify({"erro": "Campos permitidos deve ser uma lista"}), 400

        # 🔍 Monta colunas e valores dinamicamente
        colunas = []
        valores = []
        
        data_convertida = {k: parse_data_segura(v) for k, v in data.items()}

        for campo in campos_permitidos:
            if campo in data_convertida and data_convertida[campo] is not None:
                if not campo == "senha_user":
                    colunas.append(sql.SQL("{} = %s").format(sql.Identifier(campo)))
                    valores.append(data_convertida[campo])
                    continue
                senha_hash = bcrypt.hashpw(data[campo].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                colunas.append(f"{campo}=%s")
                valores.append(senha_hash)

        if not colunas:
            return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400
        # 🧱 Monta query segura
        query = sql.SQL("UPDATE {tabela} SET {set_clause} WHERE {id_coluna} = %s RETURNING *").format(
            tabela=sql.Identifier(tabela),
            set_clause=sql.SQL(", ").join(colunas),
            id_coluna=sql.Identifier(id_base)
        )

        valores.append(id_busca)  # valor do WHERE

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, tuple(valores))

        # 🔍 Verifica se algo foi atualizado
        updated = cur.fetchone()
        if not updated:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404

        conn.commit()
        colunas_retorno = [desc[0] for desc in cur.description]
        data_retorno = dict(zip(colunas_retorno, updated))

        cur.close()
        conn.close()

        return jsonify({
            "mensagem": "Item atualizado com sucesso!",
            "item_atualizado": data_retorno
        }), 200

    except OperationalError:
        return jsonify({"erro": "Erro na conexão com o banco de dados"}), 500

    except DatabaseError as e:
        return jsonify({"erro": f"Erro ao atualizar item: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400