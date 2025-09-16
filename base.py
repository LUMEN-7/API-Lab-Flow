from flask import Flask, jsonify, request
import psycopg2
import json


DATABASE_URL = ""
app = Flask(__name__)

def load_db_config():
    with open("db_info.json", "r") as f:
        return json.load(f)
    

def get_connection():
    config = load_db_config()
    return psycopg2.connect(
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"]
    )

#CRUD insumos

@app.route('/insumos', methods=['POST'])
def criar_insumo():
    data = request.get_json()
    nome_insumo = data.get("nome_insumo")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO insumo (nome_insumo) VALUES (%s) RETURNING id_insumo",
        (nome_insumo,)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Insumo criado com sucesso!", "id_insumo": new_id}), 201


@app.route('/insumos', methods=['GET'])
def listar_insumos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insumo")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    insumos = [{"id_insumo": r[0], "nome_insumo": r[1]} for r in rows]
    return jsonify(insumos)


@app.route('/insumos/<int:id_insumo>', methods=['GET'])
def obter_insumo(id_insumo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insumo WHERE id_insumo = %s", (id_insumo,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({"id_insumo": row[0], "nome_insumo": row[1]})
    else:
        return jsonify({"erro": "Insumo não encontrado"}), 404


@app.route('/insumos/<int:id_insumo>', methods=['PUT'])
def atualizar_insumo(id_insumo):
    data = request.get_json()
    novo_nome = data.get("nome_insumo")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE insumo SET nome_insumo = %s WHERE id_insumo = %s",
                (novo_nome, id_insumo))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Insumo atualizado com sucesso!"})


@app.route('/insumos/<int:id_insumo>', methods=['DELETE'])
def deletar_insumo(id_insumo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM insumo WHERE id_insumo = %s", (id_insumo,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensagem": "Insumo deletado com sucesso!"})


if __name__ == '__main__':
    app.run(debug=True)