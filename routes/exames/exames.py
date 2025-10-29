from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

exames_bp = Blueprint("exames", __name__)


# --- CRUD Exame ---
@exames_bp.route('', methods=['POST'])
@token_obrigatorio
@admin_obrigatorio
def criar_exame():
    data = request.get_json()
    return inserir_elemento_generico(tabela="exame", data= data, coluna_retorno= "id_exame")


@exames_bp.route('', methods=['GET'])
@token_obrigatorio
def listar_exames():
    return lista_itens(tabela= "exame")


@exames_bp.route('/<int:id_exame>', methods=['GET'])
@token_obrigatorio
def obter_exame(id_exame):  
    return get_item(tabela= "exame",id_base= "id_exame", id_busca= id_exame)


@exames_bp.route('/<int:id_exame>', methods=['PATCH'])
@token_obrigatorio
@admin_obrigatorio
def atualizar_exame(id_exame):
    data = request.get_json()
    campos_permitidos = ['nome_exame', 'descricao_exame']
    return atualizar_itens(tabela= "exame" ,campos_permitidos= campos_permitidos ,id_base="id_exame" ,id_busca=id_exame ,data= data )


@exames_bp.route('/<int:id_exame>', methods=['DELETE'])
@token_obrigatorio
@admin_obrigatorio
def deletar_exame(id_exame):
    return deletar_item(tabela= "insumo", id_base="id_insumo", id_busca=id_exame)