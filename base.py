from flask import Flask, jsonify, request
import psycopg2
import os
import jwt
import bcrypt
import datetime
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# Variáveis de ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY", "chave_temporaria")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def gerar_token(email_user, cpf_user, admin_user):
    payload = {
        "email_user": email_user,
        "cpf": cpf_user,
        "administrador": admin_user,
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
            request.cpf_user = data["cpf"]
            request.admin_user = data.get("administrador", "N")  # Default para "N" se não existir
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido!"}), 401

        return f(*args, **kwargs)
    return decorated


def admin_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        email = getattr(request, "email_user", None)
        if not email:
            return jsonify({"erro": "Token inválido!"}), 401
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT administrador FROM user_lab WHERE email_user=%s", (email,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if not result or result[0] != "S":
            return jsonify({"erro": "Acesso negado. Administrador necessário."}), 403
        return f(*args, **kwargs)
    return decorated


# --- CRUD Insumos ---
@app.route('/insumos', methods=['POST'])
@token_obrigatorio
@admin_obrigatorio
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
@admin_obrigatorio
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
@admin_obrigatorio
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


@app.route('/exames/<int:id_exame>', methods=['DELETE'])
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


# --- CRUD Unidade ---
@app.route('/unidades', methods=['POST'])
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

@app.route('/unidades', methods=['GET'])
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

@app.route('/unidades/<int:id_unidade>', methods=['GET'])
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

@app.route('/unidades/<int:id_unidade>', methods=['PATCH'])
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

@app.route('/unidades/<int:id_unidade>', methods=['DELETE'])
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

# --- Função usar insumos ---
@app.route("/usar_insumos", methods=["POST"])
@token_obrigatorio
def usar_insumos():
    data = request.get_json()
    id_estoque = data.get("id_estoque")
    id_cabine = data.get("id_cabine")
    insumos = data.get("insumos")

    if not id_estoque or not id_cabine:
        return jsonify({"erro": "id_estoque e id_cabine são obrigatórios"}), 400
    if not insumos or not isinstance(insumos, list):
        return jsonify({"erro": "Informe uma lista de insumos com id_insumo e quantidade"}), 400

    usuario_responsavel = request.cpf_user

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT quantidade_atual FROM estoque WHERE id_estoque = %s", (id_estoque,))
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({"erro": "Estoque não encontrado"}), 404

        quantidade_atual_estoque = resultado[0]

        total_quantidade = sum(item["quantidade"] for item in insumos)
        if quantidade_atual_estoque < total_quantidade:
            return jsonify({"erro": "Quantidade insuficiente no estoque"}), 400

        nova_quantidade = quantidade_atual_estoque - total_quantidade
        cur.execute("UPDATE estoque SET quantidade_atual = %s WHERE id_estoque = %s", (nova_quantidade, id_estoque))

        for item in insumos:
            if "id_insumo" not in item or "quantidade" not in item or item["quantidade"] <= 0:
                return jsonify({"erro": "Cada insumo precisa de id_insumo e quantidade válida"}), 400

            cur.execute("""
                INSERT INTO historico
                (cpf, id_estoque, id_cabine, id_insumo, data_hora_movimentacao, tipo_movimentacao, quantidade_insumo, origem, destino)
                VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s)
            """, (
                usuario_responsavel,
                id_estoque,
                id_cabine,
                item["id_insumo"],
                "SAÍDA",
                item["quantidade"],
                "ESTOQUE DA UNIDADE",
                "CABINE"
            ))

        conn.commit()
        return jsonify({"mensagem": "Todos os insumos usados e histórico registrado com sucesso!"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# --- Funções do histórico
@app.route("/historico", methods=["POST"])
@token_obrigatorio
def listar_historico():
    # opções: ENTRADA, SAÍDA, DESCARTE
    tipo = request.args.get("tipo")
    # formato: YYYY-MM-DD
    data_filtro = request.args.get("data")

    query = """
        SELECT id_movimentacao, cpf, id_estoque, id_cabine, id_insumo,
               data_hora_movimentacao, tipo_movimentacao, quantidade_insumo,
               origem, destino
        FROM historico
        WHERE 1=1
    """
    params = []

    if tipo:
        query += " AND tipo_movimentacao = %s"
        params.append(tipo.upper())

    if data_filtro:
        query += " AND DATE(data_hora_movimentacao) = %s"
        params.append(data_filtro)

    query += " ORDER BY data_hora_movimentacao DESC"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    historico = []
    for row in rows:
        historico.append({
            "id_movimentacao": row[0],
            "cpf": row[1],
            "id_estoque": row[2],
            "id_cabine": row[3],
            "id_insumo": row[4],
            "data_hora_movimentacao": row[5].strftime("%Y-%m-%d %H:%M:%S"),
            "tipo_movimentacao": row[6],
            "quantidade_insumo": row[7],
            "origem": row[8],
            "destino": row[9]
        })

    return jsonify(historico), 200


# --- Funções e CRUD de estoque ---
@app.route("/checar_estoque/<int:id_unidade>/<int:id_insumo>", methods=["GET"])
@token_obrigatorio
def checar_quantidade_estoque(id_unidade, id_insumo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT quantidade_atual, quantidade_minima_permitida
        FROM estoque
        WHERE id_unidade = %s AND id_insumo = %s
    """, (id_unidade, id_insumo))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"erro": "Estoque não encontrado para a unidade e insumo informados"}), 404

    quantidade_atual, quantidade_minima = row

    if quantidade_atual is None or quantidade_minima is None:
        return jsonify({"erro": "Dados de estoque inválidos"}), 500

    if quantidade_atual <= quantidade_minima:
        status = "Estoque crítico"
    elif quantidade_atual <= quantidade_minima * 1.2:
        status = "Quantidade baixa"
    else:
        status = "Estoque ok"

    return jsonify({
        "status": status,
        "quantidade": quantidade_atual,
        "limite_minimo": quantidade_minima
    }), 200


@app.route("/estoque", methods=["POST"])
@token_obrigatorio
def criar_estoque():
    data = request.get_json()
    id_insumo = data.get("id_insumo")
    id_unidade = data.get("id_unidade")
    quantidade = data.get("quantidade", 0)
    quantidade_minima = data.get("quantidade_minima_permitida", 0)
    validade = data.get("validade")

    if not id_insumo or not id_unidade:
        return jsonify({"erro": "id_insumo e id_unidade são obrigatórios"}), 400

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO estoque (id_insumo, id_unidade, quantidade_atual, quantidade_minima_permitida, validade)
            VALUES (%s, %s, %s, %s, %s) RETURNING id_estoque
        """, (id_insumo, id_unidade, quantidade, quantidade_minima, validade))
        novo_id = cur.fetchone()[0]

        # Registrar no histórico
        cur.execute("""
            INSERT INTO historico (cpf, id_estoque, data_hora_movimentacao, tipo_movimentacao, quantidade_insumo, origem, destino)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """, (request.cpf_user, novo_id, "ENTRADA", quantidade, "ARMAZÉM DASA", "ESTOQUE DA UNIDADE"))

        conn.commit()
        return jsonify({"mensagem": "Estoque criado com sucesso", "id_estoque": novo_id}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/estoque/<int:id_estoque>", methods=["GET"])
@token_obrigatorio
def obter_estoque(id_estoque):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM estoque WHERE id_estoque = %s", (id_estoque,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        colunas = ["id_estoque", "id_insumo", "id_unidade", "quantidade_atual", "quantidade_minima_permitida", "validade"]
        return jsonify(dict(zip(colunas, row))), 200
    else:
        return jsonify({"erro": "Estoque não encontrado"}), 404


@app.route("/estoque", methods=["GET"])
@token_obrigatorio
def listar_estoques():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM estoque")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    colunas = ["id_estoque", "id_insumo", "id_unidade", "quantidade_atual", "quantidade_minima_permitida", "validade"]
    return jsonify([dict(zip(colunas, row)) for row in rows]), 200


@app.route("/estoque/<int:id_estoque>", methods=["PUT"])
@token_obrigatorio
def atualizar_estoque(id_estoque):
    data = request.get_json()
    quantidade = data.get("quantidade_atual")
    quantidade_minima = data.get("quantidade_minima_permitida")
    validade = data.get("validade")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Buscar valor atual antes da atualização
        cur.execute("SELECT quantidade_atual FROM estoque WHERE id_estoque = %s", (id_estoque,))
        row = cur.fetchone()
        if not row:
            return jsonify({"erro": "Estoque não encontrado"}), 404
        quantidade_antiga = row[0]

        cur.execute("""
            UPDATE estoque
            SET quantidade_atual = COALESCE(%s, quantidade_atual),
                quantidade_minima_permitida = COALESCE(%s, quantidade_minima_permitida),
                validade = COALESCE(%s, validade)
            WHERE id_estoque = %s
        """, (quantidade, quantidade_minima, validade, id_estoque))

        # Se houve alteração de quantidade, registrar no histórico
        if quantidade is not None and quantidade != quantidade_antiga:
            tipo = "ENTRADA" if quantidade > quantidade_antiga else "SAÍDA"
            diferenca = abs(quantidade - quantidade_antiga)
            cur.execute("""
                INSERT INTO historico (cpf, id_estoque, data_hora_movimentacao, tipo_movimentacao, quantidade_insumo, origem, destino)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """, (request.cpf_user, id_estoque, tipo, diferenca, "ARMAZÉM DASA", "ESTOQUE DA UNIDADE"))

        conn.commit()
        return jsonify({"mensagem": "Estoque atualizado com sucesso"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/estoque/<int:id_estoque>", methods=["DELETE"])
@token_obrigatorio
def deletar_estoque(id_estoque):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM estoque WHERE id_estoque = %s RETURNING id_estoque", (id_estoque,))
        row = cur.fetchone()
        if not row:
            return jsonify({"erro": "Estoque não encontrado"}), 404

        # Registrar descarte no histórico
        cur.execute("""
            INSERT INTO historico (cpf, id_estoque, data_hora_movimentacao, tipo_movimentacao, quantidade_insumo, origem, destino)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """, (request.cpf_user, id_estoque, "DESCARTE", 0, "ESTOQUE DA UNIDADE", "DESCARTE"))

        conn.commit()
        return jsonify({"mensagem": "Estoque deletado com sucesso"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    

# --- CRUD usuarios ---
# --- CRUD USUÁRIO COM CAMPOS ADICIONAIS ---
@app.route("/usuarios", methods=["POST"])
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


@app.route("/usuarios/<cpf>", methods=["PATCH"])
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


@app.route("/usuarios", methods=["GET"])
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


@app.route("/usuarios/<cpf>", methods=["GET"])
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


@app.route("/usuarios/<cpf>", methods=["DELETE"])
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


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
