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

def gerar_token(email_user):
    payload = {
        "email_user": email_user,
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
            request.email_user = data["email_user"]
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
    categoria = data.get("categoria", "")
    marca = data.get("marca_insumo", "")
    desc = data.get("descricao_insumo", "")


    if not nome_insumo:
        return jsonify({"erro": "Nome do insumo é obrigatório"}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO insumo (nome_insumo, categoria, marca_insumo, descricao_insumo) VALUES (%s, %s, %s, %s) RETURNING id_insumo",
        (nome_insumo, categoria, marca, desc)
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

@app.route('/insumos/<int:id_insumo>', methods=['PATCH'])
@token_obrigatorio
def atualizar_insumo_parcial(id_insumo):
    data = request.get_json()
    campos_permitidos = ['nome_insumo', 'categoria', 'marca_insumo', 'descricao_insumo']
    colunas = []
    valores = []
    
    for campo in campos_permitidos:
        if campo in data and data[campo] is not None:
            colunas.append(f"{campo} = %s")
            valores.append(data[campo])
    
    if not colunas:
        return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

    
    valores.append(id_insumo)

    query = f"UPDATE insumo SET {', '.join(colunas)} WHERE id_insumo = %s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(valores))
    
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "Insumo não encontrado"}), 404

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


# --- CRUD Exame ---
@app.route('/exames', methods=['POST'])
@token_obrigatorio
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


@app.route('/exames', methods=['GET'])
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


@app.route('/exames/<int:id_exame>', methods=['PATCH'])
@token_obrigatorio
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


@app.route('/exames/<int:id_exame>', methods=['DELETE'])
@token_obrigatorio
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


# --- CRUD Pedido ---
@app.route('/pedidos', methods=['POST'])
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


@app.route('/pedidos', methods=['GET'])
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
            "status": p[4]
        }
        for p in pedidos
    ]
    return jsonify(resultados)


@app.route('/pedidos/<int:n_pedido>', methods=['GET'])
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


@app.route('/pedidos/<int:n_pedido>', methods=['PATCH'])
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


@app.route('/pedidos/<int:n_pedido>', methods=['DELETE'])
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
    id_unidade = data.get("id_unidade")

    if not cpf or not email or not senha:
        return jsonify({"erro": "CPF, email e senha são obrigatórios"}), 400

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user_lab WHERE cpf = %s", (cpf,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO user_lab (CPF, nome_user, cargo_user, email_user, senha_user, administrador) VALUES (%s, %s, %s, %s, %s, %s)",
            (cpf, nome, cargo, email, senha_hash, admin)
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
