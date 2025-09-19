from flask import Flask, jsonify, request
import psycopg2
import json
import jwt
import bcrypt
import datetime
from functools import wraps


DATABASE_URL = ""
app = Flask(__name__)

def load_db_config():
    with open("db_info.json", "r") as f:
        return json.load(f)
    

def get_connection():
    config = load_db_config()
    return psycopg2.connect(
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"]
    )




SECRET_KEY = load_db_config()["SECRET"]



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

        # Token vem no header Authorization: Bearer <token>
        if "Authorization" in request.headers:
            partes = request.headers["Authorization"].split(" ")
            if len(partes) == 2 and partes[0] == "Bearer":
                token = partes[1]

        if not token:
            return jsonify({"erro": "Token é obrigatório!"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # guarda o email do usuário no request (para usar dentro da rota)
            request.email_usuario = data["email_usuario"]
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido!"}), 401

        return f(*args, **kwargs)
    return decorated


#CRUD insumos

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

#CRUD fornecedor

@app.route("/fornecedores", methods=["POST"])
@token_obrigatorio
def criar_fornecedor():
    data = request.get_json()
    nome = data.get("nome_fornecedor")
    email = data.get("email_fornecedor")
    telefone = data.get("telefone")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO fornecedor (nome_fornecedor, email_fornecedor, telefone) VALUES (%s, %s, %s) RETURNING id_fornecedor",
        (nome, email, telefone)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Fornecedor criado com sucesso!", "id_fornecedor": new_id}), 201


@app.route("/fornecedores", methods=["GET"])
@token_obrigatorio
def listar_fornecedores():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_fornecedor, nome_fornecedor, email_fornecedor, telefone, ativo, data_criacao FROM fornecedor")
    fornecedores = cur.fetchall()
    cur.close()
    conn.close()

    lista = []
    for f in fornecedores:
        lista.append({
            "id_fornecedor": f[0],
            "nome_fornecedor": f[1],
            "email_fornecedor": f[2],
            "telefone": f[3],
            "ativo": f[4],
            "data_criacao": f[5].isoformat()
        })

    return jsonify(lista)


@app.route("/fornecedores/<int:id_fornecedor>", methods=["PUT"])
@token_obrigatorio
def atualizar_fornecedor(id_fornecedor):
    data = request.get_json()
    nome = data.get("nome_fornecedor")
    email = data.get("email_fornecedor")
    telefone = data.get("telefone")
    ativo = data.get("ativo")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE fornecedor 
           SET nome_fornecedor=%s, email_fornecedor=%s, telefone=%s, ativo=%s 
           WHERE id_fornecedor=%s""",
        (nome, email, telefone, ativo, id_fornecedor)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Fornecedor atualizado com sucesso!"})


@app.route("/fornecedores/<int:id_fornecedor>", methods=["DELETE"])
@token_obrigatorio
def deletar_fornecedor(id_fornecedor):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM fornecedor WHERE id_fornecedor=%s", (id_fornecedor,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Fornecedor deletado com sucesso!"})


# autenticação
@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    data = request.get_json()
    email = data.get("email_usuario")
    senha = data.get("senha_usuario")
    cpf = data.get("usuario_cpf")
    nome = data.get("nome_usuario", "")
    cargo = data.get("cargo_usuario", "") 
    admin = data.get("administrador", "N")  


    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM usuario WHERE cpf = %s", (cpf,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO usuario (cpf, nome_usuario, cargo_usuario, administrador) VALUES (%s, %s, %s, %s)",
            (cpf, nome, cargo, admin)
        )

    # Insere na tabela login
    cur.execute(
        "INSERT INTO login (usuario_cpf, email_usuario, senha_usuario) VALUES (%s, %s, %s)",
        (cpf, email, senha_hash)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Usuário criado com sucesso!", "email_usuario": email}), 201



@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email_usuario")
    senha = data.get("senha_usuario")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT email_usuario, senha_usuario FROM login WHERE email_usuario=%s",
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
    app.run(debug=True)