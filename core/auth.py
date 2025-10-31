from functools import wraps
from flask import request, jsonify
import jwt, datetime, os
from core.database import get_connection


DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.environ.get("API_SECRET")

def gerar_token(email_user, cpf_user, admin_user):
    payload = {
        "email_user": email_user,
        "cpf": cpf_user,
        "administrador": admin_user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({"erro": "Token é obrigatório!"}), 401

        try:
            data = jwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
            request.cpf_user = data["cpf"]
            request.admin_user = data.get("administrador", "N")
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido!"}), 401

        return f(*args, **kwargs)
    return decorated

def admin_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if getattr(request, "admin_user", "N") != "S":
            return jsonify({"erro": "Acesso negado. Administrador necessário."}), 403
        return f(*args, **kwargs)
    return decorated
