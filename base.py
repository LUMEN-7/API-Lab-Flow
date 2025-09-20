from flask import Flask, jsonify, request
import psycopg2
import os
import jwt
import bcrypt
import datetime
from functools import wraps

app = Flask(__name__)

# Variáveis de ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY", "chave_temporaria")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def gerar_token(email_usuario):
    payload = {
        "email_usuario": email_usuario,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def token_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            partes = request.headers["Authorization"].split(" ")
            if len(partes) == 2 and partes[0] == "Bearer":
                token = partes[1]

        if not token:
            return jsonify({"erro": "Token é obrigatório!"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.email_usuario = data["email_usuario"]
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido!"}), 401

        return f(*args, **kwargs)
    return decorated

# --- CRUD Insumos ---
@app.route('/insumos', methods=['POST'])
@token_obrigatorio
def criar_insumo():
    data = request.get_json()
    nome_insumo = data.get("nome_insumo")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO insumo (nome_insumo) VALUES (%s) RETURNING id_insumo",
        (nome_insumo,)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Insumo criado com sucesso!", "id_insumo": new_id}), 201

@app.route('/insumos', methods=['GET'])
@token_obrigatorio
def listar_insumos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insumo")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    insumos = [{"id_insumo": r[0], "nome_insumo": r[1]} for r in rows]
    return jsonify(insumos)

@app.route('/insumos/<int:id_insumo>', methods=['GET'])
@token_obrigatorio
def obter_insumo(id_insumo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insumo WHERE id_insumo = %s", (id_insumo,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({"id_insumo": row[0], "nome_insumo": row[1]})
    else:
        return jsonify({"erro": "Insumo não encontrado"}), 404

@app.route('/insumos/<int:id_insumo>', methods=['PUT'])
@token_obrigatorio
def atualizar_insumo(id_insumo):
    data = request.get_json()
    novo_nome = data.get("nome_insumo")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE insumo SET nome_insumo = %s WHERE id_insumo = %s",
                (novo_nome, id_insumo))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Insumo atualizado com sucesso!"})

@app.route('/insumos/<int:id_insumo>', methods=['DELETE'])
@token_obrigatorio
def deletar_insumo(id_insumo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM insumo WHERE id_insumo = %s", (id_insumo,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Insumo deletado com sucesso!"})


# --- Autenticação ---
@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    data = request.get_json()
    email = data.get("email_usuario")
    senha = data.get("senha_usuario")
    cpf = data.get("usuario_cpf")
    nome = data.get("nome_usuario", "")
    cargo = data.get("cargo_usuario", "") 
    admin = data.get("administrador", "N")
    status = data.get("status", "ATIVO")
    id_unidade = data.get("id_unidade")

    if not cpf or not email or not senha:
        return jsonify({"erro": "CPF, email e senha são obrigatórios"}), 400

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user_lab WHERE cpf = %s", (cpf,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO user_lab (CPF, UNIDADE_ID_unidade, nome_user, cargo_user, email_user, senha_user, status_user, administrador) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (cpf, id_unidade, nome, cargo, email, senha_hash, status, admin)
        )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Usuário criado com sucesso!", "email_usuario": email}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email_user")
    senha = data.get("senha_user")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT email_user, senha_user FROM user_lab WHERE email_user=%s",
        (email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    email_db, senha_hash_db = user

    if bcrypt.checkpw(senha.encode("utf-8"), senha_hash_db.encode("utf-8")):
        token = gerar_token(email_db)
        return jsonify({"mensagem": "Login bem-sucedido!", "token": token}), 200
    else:
        return jsonify({"erro": "Senha incorreta"}), 401

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
