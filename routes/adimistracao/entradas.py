from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

entradas_bp = Blueprint("entradas", __name__)


@entradas_bp.route('/', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_entradas():
    resposta = request.get_json()
    return inserir_elemento_generico(tabela= "entrada_estoque_armazem", data= resposta, id= "id_encomenda")

@entradas_bp.route('/', methods=['GET'])
# @token_obrigatorio
def listar_entradas():
    return lista_itens(tabela= "entrada_estoque_armazem")

@entradas_bp.route('/<int:id_entrada>', methods=['GET'])
# @token_obrigatorio
def obter_entradas(id_entrada):
    return get_item(tabela= "entrada_estoque_armazem",id_base= "id_encomenda", id_busca= id_entrada)


@entradas_bp.route('/<int:id_entrada>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_entrada(id_entrada):
    return deletar_item(tabela= "entrada_estoque_armazem", id_base="id_encomenda", id_busca=id_entrada)
    # conn = get_connection()
    # cur = conn.cursor()
    # cur.execute("DELETE FROM entradas WHERE id_insumo = %s", (id_insumo,))
    # conn.commit()
    # cur.close()
    # conn.close()
    # return jsonify({"mensagem": "Insumo deletado com sucesso!"})


@entradas_bp.route('/<int:id_entradas>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_entradas_parcial(id_entradas):
    data = request.get_json()
    campos_permitidos = ['nome_entradas', 'categoria', 'marca_entradas', 'descricao_entradas']
    colunas = []
    valores = []
    
    for campo in campos_permitidos:
        if campo in data and data[campo] is not None:
            colunas.append(f"{campo} = %s")
            valores.append(data[campo])
    
    if not colunas:
        return jsonify({"erro": "Nenhum campo válido fornecido para atualização"}), 400

    
    valores.append(id_entradas)

    query = f"UPDATE entradas SET {', '.join(colunas)} WHERE id_entradas = %s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(valores))
    
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"erro": "entradas não encontrado"}), 404

    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"mensagem": "entradas atualizado com sucesso!"})
