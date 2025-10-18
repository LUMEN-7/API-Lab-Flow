from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio

exames_bp = Blueprint("exames", __name__)


# --- CRUD Exame ---
@exames_bp.route('/', methods=['POST'])
@token_obrigatorio
@admin_obrigatorio
def criar_exame():
    data = request.get_json()
    nome_exame = data.get("nome_exame")
    descricao_exame = data.get("descricao_exame", "")

    if not nome_exame:
        return jsonify({"erro": "Nome do exame é obrigatório"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO exames (nome_exame, descricao_exame) VALUES (%s, %s) RETURNING id_exame",
        (nome_exame, descricao_exame)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Exame criado com sucesso!", "id_exame": new_id}), 201


@exames_bp.route('/', methods=['GET'])
@token_obrigatorio
def listar_exames():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_exame, nome_exame, descricao_exame FROM exames ORDER BY id_exame")
    exames = cur.fetchall()
    cur.close()
    conn.close()

    resultados = [
        {"id_exame": ex[0], "nome_exame": ex[1], "descricao_exame": ex[2]}
        for ex in exames
    ]
    return jsonify(resultados)


@exames_bp.route('/<int:id_exame>', methods=['PATCH'])
@token_obrigatorio
@admin_obrigatorio
def atualizar_exame(id_exame):
    data = request.get_json()
    campos_permitidos = ['nome_exame', 'descricao_exame']

    colunas = []
    valores = []

    for campo in campos_permitidos:
        if campo in data and data[campo] is not None:
            colunas.append(f"{campo} = %s")
            valores.append(data[campo])

    if not colunas:
        return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

    valores.append(id_exame)
    query = f"UPDATE exames SET {', '.join(colunas)} WHERE id_exame = %s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(valores))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Exame não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Exame atualizado com sucesso!"})


@exames_bp.route('/<int:id_exame>', methods=['DELETE'])
@token_obrigatorio
@admin_obrigatorio
def deletar_exame(id_exame):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM exames WHERE id_exame = %s", (id_exame,))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Exame não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Exame deletado com sucesso!"})
