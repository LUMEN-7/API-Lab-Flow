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


@entradas_bp.route('/<int:id_entrada>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_entradas(id_entrada):
    data = request.get_json()
    campos_permitidos = ["id_insumo","id_armazem","quantidade_entrada",'valor_unidade', 'lote', 'data_vencimento', 'local_armazenamento']
    return atualizar_itens(tabela= "entrada_estoque_armazem" ,campos_permitidos= campos_permitidos ,id_base="id_encomenda" ,id_busca=id_entrada ,data= data )
    
   
