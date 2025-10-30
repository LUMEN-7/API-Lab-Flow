# historico.py
# ARQUIVO TOTALMENTE REATORADO PARA SER SIMPLES

from flask import Blueprint
# Importamos a função genérica que já faz todo o trabalho pesado
from core.crud_basico import lista_itens 

historico_bp = Blueprint("historico", __name__)

@historico_bp.route("", methods=["GET"])
# @token_obrigatorio # Você pode descomentar isso
def listar_historico():
    
    # 1. Definimos as colunas que são permitidas para filtro
    # (Copiei do seu arquivo original)
    colunas_validas = {
        "id_movimentacao",
        "cpf",
        "id_estoque",
        "id_cabine",
        "data_hora_movimentacao",
        "tipo_movimentacao",
        "quantidade_insumo",
        "origem",
        "destino",
        "id_insumo",
        "id_entrada",
        "id_saida",
    }

    # 2. Chamamos a função genérica!
    # Ela já cuida de paginação, filtros dinâmicos (__in, __ilike, etc)
    # e de toda a lógica do banco de dados.
    return lista_itens(
        tabela="historico",
        colunas_validas=colunas_validas,
        default_order_by="data_hora_movimentacao" # Ordenação padrão
        # Nota: A sua função lista_itens trata 'DESC' no 'default_order_by'?
        # Se não, você pode modificá-la para aceitar "data_hora_movimentacao DESC"
        # ou ajustar a ordenação padrão.
    )