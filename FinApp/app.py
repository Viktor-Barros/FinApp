from flask import Flask, request, render_template
from db import get_connection

app = Flask(__name__)

# Rota para exibir o formulário de cadastro (GET)
@app.route("/cadastro", methods=["GET"])
def cadastro_form():
    return render_template("cadastro.html")

# Rota para receber os dados do formulário (POST)
@app.route("/cadastro", methods=["POST"])
def cadastro():
    conn = get_connection()
    cursor = conn.cursor()
    nome = request.form["nome"]
    email = request.form["email"]
    senha = request.form["senha"]

    sql = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)"
    cursor.execute(sql, (nome, email, senha))
    conn.commit()
    id_usuario = cursor.lastrowid

    cursor.close()
    conn.close()

    return f"Usuário {nome} cadastrado com sucesso! ID: {id_usuario}"

@app.route("/")
def index():
    return render_template("index.html")

# Rota para listar usuários cadastrados
@app.route("/usuarios")
def listar():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nome, email FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return str(usuarios)

if __name__ == "__main__":
    app.run(debug=True)