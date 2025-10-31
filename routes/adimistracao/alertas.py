from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route('', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_alerts():
    resposta = request.get_json()
    return inserir_elemento_generico(tabela= "alerta", data= resposta, coluna_retorno= "id_alerta")

@alerts_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_alerts():
    colunas_validas = {
        "id_alerta",
        "id_estoque",
        "id_movimentacao",
        "previsao",
        "tipo_alerta",
        "observacoes"
    }
    return lista_itens(
        tabela="alerta",
        colunas_validas=colunas_validas,
        default_order_by="id_alerta"
    )

@alerts_bp.route('/<int:id_alerta>', methods=['GET'])
# @token_obrigatorio
def obter_alerts(id_alerta):
    return get_item(tabela= "alerta",id_base= "id_alerta", id_busca= id_alerta)


@alerts_bp.route('/<int:id_alerta>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_entrada(id_alerta):
    return deletar_item(tabela= "alerta", id_base="id_alerta", id_busca=id_alerta)


@alerts_bp.route('/<int:id_alerta>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_alerts(id_alerta):
    data = request.get_json()
    campos_permitidos = [        
        "id_alerta",
        "id_estoque",
        "id_movimentacao",
        "previsao",
        "tipo_alerta",
        "observacoes"
        ]
    return atualizar_itens(tabela= "alerta" ,campos_permitidos= campos_permitidos ,id_base="id_alerta" ,id_busca=id_alerta ,data= data )
    
   
