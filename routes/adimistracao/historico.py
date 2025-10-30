from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio
import psycopg2.sql as sql
from psycopg2.extras import RealDictCursor
import math
import datetime

historico_bp = Blueprint("historico", __name__)

@historico_bp.route("", methods=["GET"]) # Mudei de POST para GET, é o correto para listagem
# @token_obrigatorio
def listar_historico():
    
    # --- 1. Obter Parâmetros ---
    # Filtros específicos do histórico
    tipo = request.args.get("tipo") # opções: ENTRADA, SAÍDA, DESCARTE
    data_filtro = request.args.get("data") # formato: YYYY-MM-DD
    
    # Filtros genéricos
    filtro_coluna = request.args.get("coluna")
    filtro_valor = request.args.get("valor")
    
    # Paginação
    try:
        pagina = int(request.args.get("pagina", 1))
        itens_por_pagina = int(request.args.get("itens_por_pagina", 20)) # default 20
        if pagina < 1 or itens_por_pagina < 1:
            raise ValueError
    except ValueError:
        return jsonify({"erro": "Parâmetros de página inválidos"}), 400

    offset = (pagina - 1) * itens_por_pagina
    
    # --- 2. Construir Cláusula WHERE ---
    params = []
    where_clauses = [sql.SQL("1=1")]
    
    if tipo:
        where_clauses.append(sql.SQL("tipo_movimentacao = %s"))
        params.append(tipo.upper())

    if data_filtro:
        where_clauses.append(sql.SQL("DATE(data_hora_movimentacao) = %s"))
        params.append(data_filtro)

    # Colunas válidas para filtro genérico
    colunas_validas = {
        "id_movimentacao",
        "cpf",
        "id_estoque",
        "id_cabine",
        "data_hora_movimentacao",
        "tipo_movimentacao",
        "quantidade_insumo",
        "origem",
        "destino",
        "id_insumo",
        "id_entrada",
        "id_saida",
    }
    if filtro_coluna and filtro_valor:
        if filtro_coluna not in colunas_validas:
            return jsonify({"erro": f"Coluna inválida para filtro: {filtro_coluna}"}), 400
        
        where_clauses.append(sql.SQL("{col} = %s").format(col=sql.Identifier(filtro_coluna)))
        params.append(filtro_valor)

    # --- 3. Conexão e Queries ---
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # --- Query 1: Contagem Total ---
        count_query_sql = sql.SQL("SELECT COUNT(*) AS total FROM historico WHERE {w}").format(
            w=sql.SQL(" AND ").join(where_clauses)
        )
        cur.execute(count_query_sql, tuple(params))
        
        resultado_contagem = cur.fetchone()
        total_items = resultado_contagem["total"] if resultado_contagem else 0
        total_pages = math.ceil(total_items / itens_por_pagina) if total_items > 0 else 1

        # --- Query 2: Dados Paginados ---
        data_query_sql = sql.SQL(
            "SELECT * FROM historico WHERE {w} "
            "ORDER BY data_hora_movimentacao DESC " # Ordem padrão
            "LIMIT %s OFFSET %s"
        ).format(
            w=sql.SQL(" AND ").join(where_clauses)
        )
        
        params.extend([itens_por_pagina, offset])
        cur.execute(data_query_sql, tuple(params))
        rows = cur.fetchall()

        # --- 4. Processar Resultados ---
        data = []
        for row_dict in rows:
            item = {}
            for key, val in row_dict.items():
                if isinstance(val, (datetime.date, datetime.datetime)):
                    item[key] = val.isoformat()
                else:
                    item[key] = val
            data.append(item)

        # --- 5. Montar Resposta ---
        metadata = {
            "pagina": pagina,
            "itens_por_pagina": itens_por_pagina,
            "total_items": total_items,
            "total_pages": total_pages
        }
        
        return jsonify({"data": data, "metadata": metadata}), 200

    except Exception as e:
        conn.rollback()
        print(f"Erro em listar_historico: {e}")
        return jsonify({"erro": "Erro interno ao listar histórico"}), 500
    finally:
        cur.close()
        conn.close()