import re
import bcrypt
from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import gerar_token
from psycopg2 import sql, Error


login_bp = Blueprint("login", __name__)



@login_bp.route("/", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"erro": "Requisição inválida. Envie um JSON válido."}), 400

        email = data.get("email_user")
        senha = data.get("senha_user")

        # Verificação de campos obrigatórios
        if not email or not senha:
            return jsonify({"erro": "E-mail e senha são obrigatórios."}), 400

        # Verificação de formato de e-mail
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"erro": "Formato de e-mail inválido."}), 400

        conn = get_connection()
        cur = conn.cursor()

        # Query segura usando psycopg2.sql
        cur.execute(
            sql.SQL("SELECT email_user, senha_user, cpf, administrador FROM user_lab WHERE email_user = %s"),
            (email,)
        )

        user = cur.fetchone()

        # Fecha antes de retornar
        cur.close()
        conn.close()

        if not user:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        email_db, senha_hash_db, cpf_db, admin_db = user

        # Verifica senha usando bcrypt
        if not bcrypt.checkpw(senha.encode("utf-8"), senha_hash_db.encode("utf-8")):
            return jsonify({"erro": "Senha incorreta."}), 401

        # Geração do token JWT
        token = gerar_token(email_db, cpf_db, admin_db)

        return jsonify({
            "usuario": {
                "email": email_db,
                "cpf": cpf_db,
                "administrador": admin_db
            },
            "mensagem": "Login bem-sucedido!",
            "token": token
        }), 200

    except Error as e:
        # Erros de banco
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 500

    except Exception as e:
        # Erros genéricos
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 500

    finally:
        # Fecha a conexão com segurança (caso algo quebre antes)
        try:
            if cur and not cur.closed:
                cur.close()
            if conn and not conn.closed:
                conn.close()
        except:
            pass
