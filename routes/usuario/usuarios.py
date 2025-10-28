from flask import Blueprint, jsonify, request
from core.database import get_connection
from core.auth import token_obrigatorio, admin_obrigatorio
from core.crud_basico import *

usuarios_bp = Blueprint("usuarios", __name__)

# --- CRUD usuarios ---
@usuarios_bp.route("/", methods=["POST"])
def criar_usuario():
    data = request.get_json()
    data_convertida = parse_data_segura(data)

    cpf=data_convertida['cpf']
    email=data_convertida['email_usuario']
    senha= data_convertida['senha_usuario']
    admin =data_convertida['admin']

    colunas = list(data_convertida.keys())
    valores = list(data_convertida.values())

    if not cpf or not email or not senha:
        return jsonify({"erro": "CPF, email e senha são obrigatórios"}), 400
    if  admin not in ["S", "N"]:
        return jsonify({"erro": "Valor de admin inválido"}), 400

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()
    query = sql.SQL("INSERT INTO {tabela} ({colunas}) VALUES ({valores}) RETURNING {coluna_retorno}").format(
        tabela=sql.Identifier("user_lab"),
        colunas=sql.SQL(', ').join(map(sql.Identifier, colunas)),
        valores=sql.SQL(', ').join(sql.Placeholder() * len(colunas)),
        coluna_retorno=sql.Identifier("email_usuario")
    )
    
    cur.execute(query, valores)
    email = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "Usuário criado com sucesso!", "email_usuario": email}), 201



@usuarios_bp.route("/<cpf>", methods=["PATCH"])
@token_obrigatorio
# @admin_obrigatorio
def atualizar_usuario(cpf):
    data = request.get_json()
    campos_permitidos = ["nome_user", "cargo_user", "email_user", "senha_user", "administrador", "telefone", "data_nascimento", "endereco"]
    return atualizar_itens(tabela= "user_lab" ,campos_permitidos= campos_permitidos ,id_base="cpf" ,id_busca=cpf ,data= data )


@usuarios_bp.route("/", methods=["GET"])
# @token_obrigatorio
# @admin_obrigatorio
def listar_usuarios():
    campos_nao_permitidos=["endereco","senha_user"]
    return lista_itens(tabela= "user_lab",campos_nao_permitidos= campos_nao_permitidos)


@usuarios_bp.route("/<cpf>", methods=["GET"])
# @token_obrigatorio
# @admin_obrigatorio
def obter_usuario(cpf):
    campos_nao_permitidos=["endereco","senha_user"]
    return get_item(tabela="user_lab", id_base="cpf", id_busca=cpf, campos_nao_permitidos=campos_nao_permitidos)


@usuarios_bp.route("/<cpf>", methods=["DELETE"])
@token_obrigatorio
# @admin_obrigatorio
def deletar_usuario(cpf):
    return deletar_item(tabela= "user_lab", id_base="cpf", id_busca=cpf)


