from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

fornecedores_bp = Blueprint("fornecedores", __name__)


@fornecedores_bp.route('', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_fornecedores():
    resposta = request.get_json()
    return inserir_elemento_generico(tabela= "fornecedor", data= resposta, coluna_retorno= "matricula")

@fornecedores_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_fornecedores():
    colunas_validas = {
        "matricula",
        "nome",
        "telefone",
        "email"
    }
    return lista_itens(
        tabela="fornecedor",
        colunas_validas=colunas_validas,
        default_order_by="matricula"
    )

@fornecedores_bp.route('/<int:matricula>', methods=['GET'])
# @token_obrigatorio
def obter_fornecedores(matricula):
    return get_item(tabela= "fornecedor",id_base= "matricula", id_busca= matricula)


@fornecedores_bp.route('/<int:matricula>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_entrada(matricula):
    return deletar_item(tabela= "fornecedor", id_base="matricula", id_busca=matricula)


@fornecedores_bp.route('/<int:matricula>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_fornecedores(matricula):
    data = request.get_json()
    campos_permitidos = [
        "matricula",
        "nome",
        "telefone",
        "email"
    ]
    return atualizar_itens(tabela= "fornecedor" ,campos_permitidos= campos_permitidos ,id_base="matricula" ,id_busca=matricula ,data= data )
    
   
