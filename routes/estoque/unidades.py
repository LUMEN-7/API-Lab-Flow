from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio

unidades_bp = Blueprint("unidades", __name__)


# --- CRUD Unidade ---
@unidades_bp.route('/', methods=['POST'])
@token_obrigatorio
@admin_obrigatorio
def criar_unidade():
    data = request.get_json()
    marca = data.get("marca_unidade")
    endereco = data.get("endereco_unidade")
    quantidade_cabine = data.get("quantidade_cabine", 0)

    if not marca or not endereco:
        return jsonify({"erro": "Marca e endereço são obrigatórios"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO unidade (marca_unidade, endereco_unidade, quantidade_cabine) VALUES (%s, %s, %s) RETURNING id_unidade",
        (marca, endereco, quantidade_cabine)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Unidade criada com sucesso!", "id_unidade": new_id}), 201

@unidades_bp.route('/', methods=['GET'])
@token_obrigatorio
def listar_unidades():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_unidade, marca_unidade, endereco_unidade, quantidade_cabine FROM unidade ORDER BY id_unidade")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    unidades = [
        {"id_unidade": r[0], "marca_unidade": r[1], "endereco_unidade": r[2], "quantidade_cabine": r[3]}
        for r in rows
    ]
    return jsonify(unidades)

@unidades_bp.route('/<int:id_unidade>', methods=['GET'])
@token_obrigatorio
def obter_unidade(id_unidade):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_unidade, marca_unidade, endereco_unidade, quantidade_cabine FROM unidade WHERE id_unidade=%s", (id_unidade,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({"id_unidade": row[0], "marca_unidade": row[1], "endereco_unidade": row[2], "quantidade_cabine": row[3]})
    else:
        return jsonify({"erro": "Unidade não encontrada"}), 404

@unidades_bp.route('/<int:id_unidade>', methods=['PATCH'])
@token_obrigatorio
@admin_obrigatorio
def atualizar_unidade(id_unidade):
    data = request.get_json()
    campos_permitidos = ['marca_unidade', 'endereco_unidade', 'quantidade_cabine']
    colunas = []
    valores = []

    for campo in campos_permitidos:
        if campo in data and data[campo] is not None:
            colunas.append(f"{campo} = %s")
            valores.append(data[campo])

    if not colunas:
        return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

    valores.append(id_unidade)
    query = f"UPDATE unidade SET {', '.join(colunas)} WHERE id_unidade = %s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(valores))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Unidade não encontrada"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Unidade atualizada com sucesso!"})

@unidades_bp.route('/<int:id_unidade>', methods=['DELETE'])
@token_obrigatorio
@admin_obrigatorio
def deletar_unidade(id_unidade):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM unidade WHERE id_unidade = %s", (id_unidade,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Unidade não encontrada"}), 404
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Unidade deletada com sucesso!"})
