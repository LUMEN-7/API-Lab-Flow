from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

armazem_bp = Blueprint("armazem", __name__)


@armazem_bp.route('', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_armazem():
    resposta = request.get_json()
    return inserir_elemento_generico(tabela= "armazem", data= resposta, coluna_retorno= "id_armazem")

@armazem_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_armazem():
    colunas_validas = {
        "id_armazem",
        "capacidade_total",
        "ocupacao_atual",
        "endereco_armazem"
    }
    return lista_itens(
        tabela="armazem",
        colunas_validas=colunas_validas,
        default_order_by="id_armazem"
    )

@armazem_bp.route('/<int:id_armazem>', methods=['GET'])
# @token_obrigatorio
def obter_armazem(id_armazem):
    return get_item(tabela= "armazem",id_base= "id_armazem", id_busca= id_armazem)


@armazem_bp.route('/<int:id_armazem>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_entrada(id_armazem):
    return deletar_item(tabela= "armazem", id_base="id_armazem", id_busca=id_armazem)


@armazem_bp.route('/<int:id_armazem>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_armazem(id_armazem):
    data = request.get_json()
    campos_permitidos = [               
        "id_armazem",
        "capacidade_total",
        "ocupacao_atual",
        "endereco_armazem"
        ]
    return atualizar_itens(tabela= "armazem" ,campos_permitidos= campos_permitidos ,id_base="id_armazem" ,id_busca=id_armazem ,data= data )
    
   
