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
    colunas_validas = {"n_pedido", "user_lab_cpf", "grau_urgencia", "data_pedido", "status"}
    return lista_itens(
        tabela="pedido", 
        colunas_validas=colunas_validas, 
        default_order_by="n_pedido" # Coluna de ordenação padrão
    )

@pedidos_bp.route('/lookup', methods=['GET'])
# @token_obrigatorio
def listar_pedidos_lookup():
    """
    Retorna uma lista simples (ID e Nome) de todos os insumos.
    Otimizado para preencher dropdowns (<select>).
    """
# --- 1. Obter Parâmetros de Filtro ---
    filtro_coluna = request.args.get("coluna")
    filtro_valor = request.args.get("valor")
    
    colunas_validas_filtro = {"grau_urgencia", "cpf", "status", "unidade_destino", "data_pedido"}
    
    params = []
    where_clauses = [sql.SQL("1=1")] 
    
    # --- 2. Construir Cláusula WHERE Dinâmica ---
    if filtro_coluna and filtro_valor:
        if filtro_coluna not in colunas_validas_filtro:
            return jsonify({"erro": f"Coluna inválida para filtro: {filtro_coluna}"}), 400
        
        # --- CORREÇÃO 1: Sintaxe do ILIKE ---
        # (Corrigindo o bug da nossa conversa anterior)
        if filtro_coluna == 'grau_urgencia':
            # Use a concatenação SQL '||' para o LIKE/ILIKE
            # '%%' é a forma de escapar um '%' literal para o psycopg2
            where_clauses.append(sql.SQL("grau_urgencia ILIKE '%%' || %s || '%%'"))
            # O parâmetro é apenas o valor PURO, sem os '%'
            params.append(filtro_valor)
        elif filtro_coluna == 'data_pedido':
            # Adicionando tratamento para datas
            where_clauses.append(sql.SQL("DATE(data_pedido) = %s"))
            params.append(filtro_valor)
        else:
            # Filtro exato para outras colunas
            where_clauses.append(sql.SQL("{col} = %s").format(col=sql.Identifier(filtro_coluna)))
            params.append(filtro_valor)

    # --- 3. Montar e Executar a Query ---
    
    # --- CORREÇÃO 2: Query SQL (O erro que você viu) ---
    # 1. O SELECT deve ter colunas fixas (ex: n_pedido, status).
    #    NÃO deve incluir '{w}' no SELECT.
    # 2. A tabela (t) deve ser "pedido", não "insumo".
    query = sql.SQL("SELECT n_pedido, status, grau_urgencia FROM {t} WHERE {w} ORDER BY n_pedido").format(
        t=sql.Identifier("pedido"), # CORRIGIDO: de "insumo" para "pedido"
        w=sql.SQL(" AND ").join(where_clauses) # 'w' é usado APENAS AQUI
    )
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Passa a lista de parâmetros para o execute para segurança
        print(f"Query: {query.as_string(conn)}") # Para debug
        print(f"Params: {params}") # Para debug
        
        # Agora sim: o número de %s na query bate com o len(params)
        cur.execute(query, tuple(params)) 
        
        pedidos = cur.fetchall()
        
        print(f"Resultados: {pedidos}")
        return jsonify(pedidos), 200
        
    except Exception as e:
        print(f"Erro em /pedidos/lookup: {e}")
        # Log mais detalhado
        print(f"Query que falhou: {query.as_string(conn)}")
        print(f"Parâmetros da falha: {params}")
        return jsonify({"erro": f"Erro ao buscar lista de pedidos: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()



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

