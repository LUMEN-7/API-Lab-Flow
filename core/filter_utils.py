from sqlalchemy.orm import Query
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import Column
from typing import Dict, Any

def _convert_to_numeric(value_str: str) -> float:
    """Tenta converter um valor string para float. Levanta ValueError se falhar."""
    if value_str is None:
        raise ValueError("Valor não pode ser nulo para operador numérico")
    try:
        return float(value_str)
    except (ValueError, TypeError):
        raise ValueError(f"Valor '{value_str}' não é um número válido.")

def apply_dynamic_filters(query: Query, model: DeclarativeMeta, filter_params: Dict[str, Any]) -> Query:
    """
    Aplica filtros dinâmicos a uma query SQLAlchemy baseada em parâmetros de URL.

    Suporta operadores no formato: <campo>__<operador>
    Ex: ?nome_insumo__ilike=para&quantidade__gt=10

    :param query: A query SQLAlchemy inicial (ex: db.session.query(Insumo))
    :param model: A classe do modelo SQLAlchemy (ex: Insumo)
    :param filter_params: Um dicionário de parâmetros (ex: request.args)
    :return: A query SQLAlchemy modificada com os filtros.
    :raises AttributeError: Se um campo não existir no modelo.
    :raises ValueError: Se um operador for desconhecido ou a conversão de tipo falhar.
    """
    
    for key, value in filter_params.items():
        # Ignora chaves de paginação ou outros parâmetros não-filtro
        if key in ['pagina', 'itens_por_pagina']:
            continue
            
        parts = key.split('__')
        field_name = parts[0]
        
        # Define o operador
        if len(parts) == 1:
            operator = 'exact' # Operador padrão (igualdade)
        elif len(parts) == 2:
            operator = parts[1]
        else:
            # Ignora filtros malformados (ou poderia levantar um erro)
            continue 

        # --- Validação de Segurança ---
        # Verifica se o campo realmente existe no modelo
        if not hasattr(model, field_name):
            raise AttributeError(f"Campo '{field_name}' não encontrado no modelo '{model.__name__}'.")
        
        column: Column = getattr(model, field_name)

        # --- Lógica dos Operadores ---
        # Usamos match/case para uma lógica limpa
        match operator:
            case 'exact':
                query = query.filter(column == value)
            
            case 'in':
                # Solução direta para o N+1: ?id_entrada__in=5,10,15
                values_list = value.split(',')
                query = query.filter(column.in_(values_list))
            
            case 'ilike':
                # Ex: ?nome_insumo__ilike=parafuso
                query = query.filter(column.ilike(f'%{value}%'))
            
            case 'gt':
                # Ex: ?quantidade__gt=10
                numeric_value = _convert_to_numeric(value)
                query = query.filter(column > numeric_value)

            case 'gte':
                # Ex: ?quantidade__gte=10
                numeric_value = _convert_to_numeric(value)
                query = query.filter(column >= numeric_value)
            
            case 'lt':
                # Ex: ?quantidade__lt=100
                numeric_value = _convert_to_numeric(value)
                query = query.filter(column < numeric_value)
            
            case 'lte':
                # Ex: ?quantidade__lte=100
                numeric_value = _convert_to_numeric(value)
                query = query.filter(column <= numeric_value)
            
            case _:
                # Operador não suportado
                raise ValueError(f"Operador desconhecido: '{operator}'")
    
    return query