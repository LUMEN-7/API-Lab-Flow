from datetime import datetime, date
from flask import jsonify
from core.database import get_connection
from psycopg2 import sql, DatabaseError
from psycopg2.errors import UndefinedTable, SyntaxError, OperationalError



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

            placeholders = ', '.join(['%s'] * len(colunas))
            nomes_colunas = ', '.join(colunas)

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


def lista_itens(tabela):
    try:
        # Verificações básicas
        if not tabela or not isinstance(tabela, str):
            return jsonify({"erro": "Nome da tabela inválido"}), 400

        conn = get_connection()
        cur = conn.cursor()

        # Consulta segura com psycopg2.sql para evitar SQL Injection
        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(tabela))
        cur.execute(query)
        rows = cur.fetchall()

        # Se não houver resultados
        if not rows:
            return jsonify({"erro": "Nenhum registro encontrado"}), 404

        # Captura os nomes das colunas dinamicamente
        colunas = [desc[0] for desc in cur.description]

        cur.close()
        conn.close()

        # Converte para lista de dicionários
        data = [dict(zip(colunas, row)) for row in rows]

        return jsonify(data), 200

    except OperationalError:
        return jsonify({"erro": "Erro na conexão com o banco de dados"}), 500

    except DatabaseError as e:
        return jsonify({"erro": f"Erro ao executar consulta: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 400

    
def get_item(tabela, id_base, id_busca):
    try:
        # Verificações básicas
        if not all([tabela, id_base, id_busca]):
            return jsonify({"erro": "Parâmetros inválidos"}), 400

        if not isinstance(tabela, str) or not isinstance(id_base, str):
            return jsonify({"erro": "Nome da tabela ou coluna inválido"}), 400

        conn = get_connection()
        cur = conn.cursor()

        # Consulta segura — previne SQL injection
        query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
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
                colunas.append(sql.SQL("{} = %s").format(sql.Identifier(campo)))
                valores.append(data_convertida[campo])

        if not colunas:
            return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400
        print(valores)
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