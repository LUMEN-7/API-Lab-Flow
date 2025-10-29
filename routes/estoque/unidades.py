from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

unidades_bp = Blueprint("unidades", __name__)


# --- CRUD Unidade ---
@unidades_bp.route('', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_unidade():   
    data = request.get_json()
    return inserir_elemento_generico(tabela="unidade", data= data, coluna_retorno= "id_unidade")


@unidades_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_unidades():
    return lista_itens(tabela= "unidade")


@unidades_bp.route('/<int:id_unidade>', methods=['GET'])
# @token_obrigatorio
def obter_unidade(id_unidade):  
    return get_item(tabela= "unidade",id_base= "id_unidade", id_busca= id_unidade)


@unidades_bp.route('/<int:id_unidade>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_unidade(id_unidade):
    data = request.get_json()
    campos_permitidos = ['marca_unidade', 'endereco_unidade', 'quantidade_cabine']
    return atualizar_itens(tabela= "unidade" ,campos_permitidos= campos_permitidos ,id_base="id_unidade" ,id_busca=id_unidade ,data= data )


@unidades_bp.route('/<int:id_unidade>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_unidade(id_unidade):
    return deletar_item(tabela= "unidade", id_base="id_unidade", id_busca=id_unidade)
