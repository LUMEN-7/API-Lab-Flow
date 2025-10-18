from flask import Flask 
from flask_cors import CORS 
from routes.usuario.usuarios import usuarios_bp
from routes.usuario.login import login_bp
from routes.exames.exames import exames_bp
from routes.estoque.insumos import insumos_bp
from routes.estoque.unidades import unidades_bp
from routes.estoque.estoque import estoque_bp 
from routes.adimistracao.historico import historico_bp
from routes.adimistracao.pedidos import pedidos_bp
from routes.adimistracao.alertas import alertas_bp
from routes.adimistracao.entradas import entradas_bp
from routes.adimistracao.saidas import saidas_bp

app = Flask(__name__)
CORS(app)

# Registro dos módulos (Blueprints)
app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
app.register_blueprint(login_bp, url_prefix="/login")

app.register_blueprint(exames_bp, url_prefix="/exames")

app.register_blueprint(insumos_bp, url_prefix="/insumos")
app.register_blueprint(unidades_bp, url_prefix="/unidades")
app.register_blueprint(estoque_bp, url_prefix="/estoque")

app.register_blueprint(historico_bp, url_prefix="/historico")
app.register_blueprint(pedidos_bp, url_prefix="/pedidos")
app.register_blueprint(alertas_bp, url_prefix="/alertas") 
app.register_blueprint(entradas_bp, url_prefix="/entradas") 
app.register_blueprint(saidas_bp, url_prefix="/saidas")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
