from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

pedidos_bp = Blueprint("pedidos", __name__)


# --- CRUD Pedido ---
@pedidos_bp.route('', methods=['POST'])
# @token_obrigatorio
def criar_pedido():
    data = request.get_json()
    return inserir_elemento_generico(tabela="pedido", data= data, coluna_retorno= "n_pedido")


@pedidos_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_pedidos():
    return lista_itens(tabela= "pedido")


@pedidos_bp.route('/<int:n_pedido>', methods=['GET'])
# @token_obrigatorio
def obter_pedido(n_pedido):
    return get_item(tabela="pedido", id_base="n_pedido", id_busca=n_pedido)


@pedidos_bp.route('/<int:n_pedido>', methods=['PATCH'])
# @token_obrigatorio
def atualizar_pedido(n_pedido):
    data = request.get_json()
    campos_permitidos =['n_pedido', 'user_lab_cpf', 'grau_urgencia', 'data_pedido', 'status', 'unidade_destino']
    return atualizar_itens(tabela= "pedido" ,campos_permitidos= campos_permitidos ,id_base="n_pedido" ,id_busca=n_pedido ,data= data )


@pedidos_bp.route('/<int:n_pedido>', methods=['DELETE'])
# @token_obrigatorio
def deletar_pedido(n_pedido):
    return deletar_item(tabela= "pedido", id_base="n_pedido", id_busca=n_pedido)

