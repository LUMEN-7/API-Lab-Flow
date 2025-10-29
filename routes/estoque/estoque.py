from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

estoque_bp = Blueprint("estoque", __name__)

# --- Funções e CRUD de estoque ---


@estoque_bp.route("", methods=["POST"])
# @token_obrigatorio
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


@estoque_bp.route("/<int:id_estoque>", methods=["GET"])
# @token_obrigatorio
def obter_estoque(id_estoque):
    return get_item(tabela= "estoque",id_base= "id_estoque", id_busca= id_estoque)


@estoque_bp.route("", methods=["GET"])
# @token_obrigatorio
def listar_estoques():
    return lista_itens(tabela= "estoque")


@estoque_bp.route("/<int:id_estoque>", methods=["PATCH"])
# @token_obrigatorio
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


@estoque_bp.route("/<int:id_estoque>", methods=["DELETE"])
# @token_obrigatorio
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
    

@estoque_bp.route("/checar_estoque/<int:id_unidade>/<int:id_insumo>", methods=["GET"])
# @token_obrigatorio
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

