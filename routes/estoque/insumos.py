from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

insumos_bp = Blueprint("insumos", __name__)



# --- CRUD Insumos ---
@insumos_bp.route('', methods=['POST'])
# @token_obrigatorio
# @admin_obrigatorio
def criar_insumo():
    data = request.get_json()
    return inserir_elemento_generico(tabela= "insumo", data= data, coluna_retorno= "id_insumo")

@insumos_bp.route('', methods=['GET'])
# @token_obrigatorio
def listar_insumos():
    colunas_validas = {"id_insumo", "nome_insumo", "categoria", "marca_insumo"}
    return lista_itens(
        tabela="insumo",
        colunas_validas=colunas_validas,
        default_order_by="nome_insumo"
    )

@insumos_bp.route('/insumos-lista', methods=['GET'])
# @token_obrigatorio
def listar_insumos_lookup():
    """
    Retorna uma lista simples (ID e Nome) de todos os insumos.
    Otimizado para preencher dropdowns (<select>).
    """
# --- 1. Obter Parâmetros de Filtro ---
    filtro_coluna = request.args.get("coluna")
    filtro_valor = request.args.get("valor")
    
    colunas_validas_filtro = {"id_insumo", "nome_insumo", "categoria", "marca_insumo"}
    
    params = []
    where_clauses = [sql.SQL("1=1")] 
    
    # --- 2. Construir Cláusula WHERE Dinâmica ---
    if filtro_coluna and filtro_valor:
        if filtro_coluna not in colunas_validas_filtro:
            return jsonify({"erro": f"Coluna inválida para filtro: {filtro_coluna}"}), 400
        
        # --- CORREÇÃO 1: Sintaxe do ILIKE ---
        # (Corrigindo o bug da nossa conversa anterior)
        if filtro_coluna == 'nome_insumo':
            # Use a concatenação SQL '||' para o LIKE/ILIKE
            # '%%' é a forma de escapar um '%' literal para o psycopg2
            where_clauses.append(sql.SQL("nome_insumo ILIKE '%%' || %s || '%%'"))
            # O parâmetro é apenas o valor PURO, sem os '%'
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
    query = sql.SQL("SELECT id_insumo, nome_insumo FROM {t} WHERE {w} ORDER BY id_insumo").format(
        t=sql.Identifier("insumo"), # CORRIGIDO: de "insumo" para "pedido"
        w=sql.SQL(" AND ").join(where_clauses) # 'w' é usado APENAS AQUI
    )
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Passa a lista de parâmetros para o execute para segurança
        # print(f"Query: {query.as_string(conn)}") # Para debug
        # print(f"Params: {params}") # Para debug
        
        # Agora sim: o número de %s na query bate com o len(params)
        cur.execute(query, tuple(params)) 
        
        insumos = cur.fetchall()
        
        # print(f"Resultados: {insumos}")
        return jsonify(insumos), 200
        
    except Exception as e:
        # print(f"Erro em /pedidos/lookup: {e}")
        # # Log mais detalhado
        # print(f"Query que falhou: {query.as_string(conn)}")
        # print(f"Parâmetros da falha: {params}")
        return jsonify({"erro": f"Erro ao buscar lista de pedidos: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


@insumos_bp.route('/<int:id_insumo>', methods=['GET'])
# @token_obrigatorio
def obter_insumo(id_insumo):    
    return get_item(tabela="insumo", id_base="id_insumo", id_busca=id_insumo)


@insumos_bp.route('/<int:id_insumo>', methods=['PATCH'])
# @token_obrigatorio
# @admin_obrigatorio
def atualizar_insumo_parcial(id_insumo):
    data = request.get_json()
    campos_permitidos = ['nome_insumo', 'categoria', 'marca_insumo', 'descricao_insumo']
    return atualizar_itens(tabela= "insumo" ,campos_permitidos= campos_permitidos ,id_base="id_insumo" ,id_busca=id_insumo ,data= data )

@insumos_bp.route('/<int:id_insumo>', methods=['DELETE'])
# @token_obrigatorio
# @admin_obrigatorio
def deletar_insumo(id_insumo):
    return deletar_item(tabela= "insumo", id_base="id_insumo", id_busca=id_insumo)


# --- Função usar insumos ---
@insumos_bp.route("/usar_insumos", methods=["POST"])
# @token_obrigatorio
def usar_insumos():
    data = request.get_json()
    id_estoque = data.get("id_estoque")
    id_cabine = data.get("id_cabine")
    insumos = data.get("insumos")

    if not id_estoque or not id_cabine:
        return jsonify({"erro": "id_estoque e id_cabine são obrigatórios"}), 400
    if not insumos or not isinstance(insumos, list):
        return jsonify({"erro": "Informe uma lista de insumos com id_insumo e quantidade"}), 400

    usuario_responsavel = request.cpf_user

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT quantidade_atual FROM estoque WHERE id_estoque = %s", (id_estoque,))
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({"erro": "Estoque não encontrado"}), 404

        quantidade_atual_estoque = resultado[0]

        total_quantidade = sum(item["quantidade"] for item in insumos)
        if quantidade_atual_estoque < total_quantidade:
            return jsonify({"erro": "Quantidade insuficiente no estoque"}), 400

        nova_quantidade = quantidade_atual_estoque - total_quantidade
        cur.execute("UPDATE estoque SET quantidade_atual = %s WHERE id_estoque = %s", (nova_quantidade, id_estoque))

        for item in insumos:
            if "id_insumo" not in item or "quantidade" not in item or item["quantidade"] <= 0:
                return jsonify({"erro": "Cada insumo precisa de id_insumo e quantidade válida"}), 400

            cur.execute("""
                INSERT INTO historico
                (cpf, id_estoque, id_cabine, id_insumo, data_hora_movimentacao, tipo_movimentacao, quantidade_insumo, origem, destino)
                VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s)
            """, (
                usuario_responsavel,
                id_estoque,
                id_cabine,
                item["id_insumo"],
                "SAÍDA",
                item["quantidade"],
                "ESTOQUE DA UNIDADE",
                "CABINE"
            ))

        conn.commit()
        return jsonify({"mensagem": "Todos os insumos usados e histórico registrado com sucesso!"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        cur.close()
        conn.close()
