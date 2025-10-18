from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio

pedidos_bp = Blueprint("pedidos", __name__)


# --- CRUD Pedido ---
@pedidos_bp.route('/', methods=['POST'])
@token_obrigatorio
def criar_pedido():
    data = request.get_json()
    user_lab_cpf = data.get("user_lab_cpf")
    grau_urgencia = data.get("grau_urgencia", "")
    status = data.get("status", "PENDENTE")

    if not user_lab_cpf:
        return jsonify({"erro": "CPF do usuário é obrigatório"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pedido (user_lab_cpf, grau_urgencia, status) VALUES (%s, %s, %s) RETURNING n_pedido",
        (user_lab_cpf, grau_urgencia, status)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Pedido criado com sucesso!", "n_pedido": new_id}), 201


@pedidos_bp.route('/', methods=['GET'])
@token_obrigatorio
def listar_pedidos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT n_pedido, user_lab_cpf, grau_urgencia, data_pedido, status FROM pedido ORDER BY n_pedido")
    pedidos = cur.fetchall()
    cur.close()
    conn.close()

    resultados = [
        {
            "n_pedido": p[0],
            "user_lab_cpf": p[1],
            "grau_urgencia": p[2],
            "data_pedido": p[3].isoformat(),
            "status": p[4],
            "unidade_destino": p[5]
        }
        for p in pedidos
    ]
    return jsonify(resultados)


@pedidos_bp.route('/<int:n_pedido>', methods=['GET'])
@token_obrigatorio
def obter_pedido(n_pedido):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT n_pedido, user_lab_cpf, grau_urgencia, data_pedido, status FROM pedido WHERE n_pedido = %s",
        (n_pedido,)
    )
    pedido = cur.fetchone()
    cur.close()
    conn.close()

    if not pedido:
        return jsonify({"erro": "Pedido não encontrado"}), 404

    return jsonify({
        "n_pedido": pedido[0],
        "user_lab_cpf": pedido[1],
        "grau_urgencia": pedido[2],
        "data_pedido": pedido[3].isoformat(),
        "status": pedido[4]
    })


@pedidos_bp.route('/<int:n_pedido>', methods=['PATCH'])
@token_obrigatorio
def atualizar_pedido(n_pedido):
    data = request.get_json()
    campos_permitidos = ['grau_urgencia', 'status']

    colunas = []
    valores = []

    for campo in campos_permitidos:
        if campo in data and data[campo] is not None:
            colunas.append(f"{campo} = %s")
            valores.append(data[campo])

    if not colunas:
        return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

    valores.append(n_pedido)
    query = f"UPDATE pedido SET {', '.join(colunas)} WHERE n_pedido = %s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(valores))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Pedido não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Pedido atualizado com sucesso!"})


@pedidos_bp.route('/<int:n_pedido>', methods=['DELETE'])
@token_obrigatorio
def deletar_pedido(n_pedido):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pedido WHERE n_pedido = %s", (n_pedido,))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Pedido não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Pedido deletado com sucesso!"})

