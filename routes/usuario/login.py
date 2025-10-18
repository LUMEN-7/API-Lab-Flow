import bcrypt
from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import gerar_token

login_bp = Blueprint("login", __name__)



@login_bp.route("/", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email_user")
    senha = data.get("senha_user")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT email_user, senha_user, cpf, administrador FROM user_lab WHERE email_user=%s",
        (email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    email_db, senha_hash_db, cpf_db, admin_db = user

    if bcrypt.checkpw(senha.encode("utf-8"), senha_hash_db.encode("utf-8")):
        token = gerar_token(email_db, cpf_db, admin_db)
        return jsonify({"mensagem": "Login bem-sucedido!", "token": token}), 200
    else:
        return jsonify({"erro": "Senha incorreta"}), 401
