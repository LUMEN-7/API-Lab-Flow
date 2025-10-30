from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

saidas_bp = Blueprint("saidas", __name__)



@saidas_bp.route('', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_saidas():
    resposta = request.get_json()
    return inserir_elemento_generico(tabela= "saida_estoque_armazem_pedido", data= resposta, coluna_retorno= "n_entrega")

@saidas_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_saidas():
    colunas_validas = {
        "n_entrega", 
        "id_armazem",
        "n_pedido",
        "data_saida",
        "status"
    }
    
    return lista_itens(
        tabela="saida_estoque_armazem_pedido",
        colunas_validas=colunas_validas,
        default_order_by="n_entrega"
    )

@saidas_bp.route('/<int:id_saida>', methods=['GET'])
# @token_obrigatorio
def obter_saidas(id_saida):
    return get_item(tabela= "saida_estoque_armazem_pedido",id_base= "n_entrega", id_busca= id_saida)


@saidas_bp.route('/<int:id_saida>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_saida(id_saida):
    return deletar_item(tabela= "saida_estoque_armazem_pedido", id_base="n_entrega", id_busca=id_saida)


@saidas_bp.route('/<int:id_saida>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_saidas(id_saida):
    data = request.get_json()
    campos_permitidos = [        
        "n_entrega", 
        "id_armazem",
        "n_pedido",
        "data_saida",
        "status"
        ]
    return atualizar_itens(tabela= "saida_estoque_armazem_pedido" ,campos_permitidos= campos_permitidos ,id_base="n_entrega" ,id_busca=id_saida ,data= data )