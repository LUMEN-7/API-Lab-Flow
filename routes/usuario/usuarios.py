from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio

usuarios_bp = Blueprint("usuarios", __name__)

# --- CRUD usuarios ---
@usuarios_bp.route("/", methods=["POST"])
def criar_usuario():
    data = request.get_json()
    email = data.get("email_usuario")
    senha = data.get("senha_usuario")
    cpf = data.get("usuario_cpf")
    nome = data.get("nome_usuario", "")
    cargo = data.get("cargo_usuario", "")
    admin = data.get("administrador", "N")
    telefone = data.get("telefone")
    data_nascimento = data.get("data_nascimento")  # formato 'YYYY-MM-DD'
    endereco = data.get("endereco")

    if not cpf or not email or not senha:
        return jsonify({"erro": "CPF, email e senha são obrigatórios"}), 400
    if admin not in ["S", "N"]:
        return jsonify({"erro": "Valor de admin inválido"}), 400

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user_lab WHERE cpf = %s", (cpf,))
    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO user_lab 
            (CPF, nome_user, cargo_user, email_user, senha_user, administrador, telefone, data_nascimento, endereco)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (cpf, nome, cargo, email, senha_hash, admin, telefone, data_nascimento, endereco)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"mensagem": "Usuário criado com sucesso!", "email_usuario": email}), 201
    else:
        return jsonify({"erro": f"Usuário com CPF {cpf} já existe"}), 400


@usuarios_bp.route("/<cpf>", methods=["PATCH"])
@token_obrigatorio
def atualizar_usuario(cpf):
    if request.cpf_user != cpf and not getattr(request, "admin_user", False):
        return jsonify({"erro": "Sem permissão"}), 403

    data = request.get_json()
    campos_permitidos = ["nome_user", "cargo_user", "email_user", "senha_user", "administrador", "telefone", "data_nascimento", "endereco"]
    colunas = []
    valores = []

    for campo in campos_permitidos:
        if campo in data and data[campo] is not None:
            if campo == "senha_user":
                senha_hash = bcrypt.hashpw(data[campo].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                colunas.append(f"{campo}=%s")
                valores.append(senha_hash)
            else:
                colunas.append(f"{campo}=%s")
                valores.append(data[campo])

    if not colunas:
        return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

    valores.append(cpf)
    query = f"UPDATE user_lab SET {', '.join(colunas)} WHERE cpf=%s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(valores))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Usuário não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Usuário atualizado com sucesso!"}), 200


@usuarios_bp.route("/", methods=["GET"])
@token_obrigatorio
def listar_usuarios():
    conn = get_connection()
    cur = conn.cursor()

    if getattr(request, "admin_user", False):
        cur.execute("""
            SELECT cpf, nome_user, cargo_user, email_user, administrador, telefone, data_nascimento, endereco 
            FROM user_lab
        """)
    else:
        cur.execute("""
            SELECT cpf, nome_user, cargo_user, email_user, administrador, telefone, data_nascimento, endereco 
            FROM user_lab 
            WHERE cpf=%s
        """, (request.cpf_user,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    usuarios = [
        {
            "cpf": r[0], "nome_user": r[1], "cargo_user": r[2], "email_user": r[3], "administrador": r[4],
            "telefone": r[5], "data_nascimento": r[6], "endereco": r[7]
        }
        for r in rows
    ]
    return jsonify(usuarios), 200


@usuarios_bp.route("/<cpf>", methods=["GET"])
@token_obrigatorio
def obter_usuario(cpf):
    if request.cpf_user != cpf and not getattr(request, "admin_user", False):
        return jsonify({"erro": "Sem permissão"}), 403

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cpf, nome_user, cargo_user, email_user, administrador, telefone, data_nascimento, endereco 
        FROM user_lab 
        WHERE cpf=%s
    """, (cpf,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    usuario = {
        "cpf": row[0], "nome_user": row[1], "cargo_user": row[2], "email_user": row[3], "administrador": row[4],
        "telefone": row[5], "data_nascimento": row[6], "endereco": row[7]
    }
    return jsonify(usuario), 200


@usuarios_bp.route("/<cpf>", methods=["DELETE"])
@token_obrigatorio
def deletar_usuario(cpf):
    if request.cpf_user != cpf and not getattr(request, "admin_user", False):
        return jsonify({"erro": "Sem permissão"}), 403

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_lab WHERE cpf=%s", (cpf,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Usuário não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Usuário deletado com sucesso!"}), 200


