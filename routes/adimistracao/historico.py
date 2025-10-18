from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio

historico_bp = Blueprint("historico", __name__)


# --- Funções do histórico
@historico_bp.route("/", methods=["POST"])
@token_obrigatorio
def listar_historico():
    # opções: ENTRADA, SAÍDA, DESCARTE
    tipo = request.args.get("tipo")
    # formato: YYYY-MM-DD
    data_filtro = request.args.get("data")

    query = """
        SELECT id_movimentacao, cpf, id_estoque, id_cabine, id_insumo,
               data_hora_movimentacao, tipo_movimentacao, quantidade_insumo,
               origem, destino
        FROM historico
        WHERE 1=1
    """
    params = []

    if tipo:
        query += " AND tipo_movimentacao = %s"
        params.append(tipo.upper())

    if data_filtro:
        query += " AND DATE(data_hora_movimentacao) = %s"
        params.append(data_filtro)

    query += " ORDER BY data_hora_movimentacao DESC"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    historico = []
    for row in rows:
        historico.append({
            "id_movimentacao": row[0],
            "cpf": row[1],
            "id_estoque": row[2],
            "id_cabine": row[3],
            "id_insumo": row[4],
            "data_hora_movimentacao": row[5].strftime("%Y-%m-%d %H:%M:%S"),
            "tipo_movimentacao": row[6],
            "quantidade_insumo": row[7],
            "origem": row[8],
            "destino": row[9]
        })

    return jsonify(historico), 200
