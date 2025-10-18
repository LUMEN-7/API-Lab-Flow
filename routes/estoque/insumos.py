from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio

insumos_bp = Blueprint("insumos", __name__)



# --- CRUD Insumos ---
@insumos_bp.route('/', methods=['POST'])
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

@insumos_bp.route('/', methods=['GET'])
@token_obrigatorio
def listar_insumos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insumo")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    colunas = ["id_insumo", "nome_insumo", "categoria", "marca_insumo", "descricao_insumos", "matricula_fornecedor"]
    return jsonify(dict(zip(colunas, rows))), 200

@insumos_bp.route('/<int:id_insumo>', methods=['GET'])
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

@insumos_bp.route('/<int:id_insumo>', methods=['PATCH'])
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

@insumos_bp.route('/<int:id_insumo>', methods=['DELETE'])
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


# --- Função usar insumos ---
@insumos_bp.route("/usar_insumos", methods=["POST"])
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
