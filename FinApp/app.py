from flask import Flask, request, render_template, flash
from db import get_connection
import smtplib

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/cadastro", methods=["GET"])
def cadastro_form():
    return render_template("cadastro.html")

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

@app.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    senha = request.form["senha"]
    # Adicione a lógica de autenticação aqui
    return f"Tentativa de login para: {email}"

@app.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    if request.method == "GET":
        return render_template("recuperar-senha.html")
    else:
        email = request.form["email"]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario:
            # Simulação de envio de e-mail (substitua pelo seu servidor SMTP real)
            link = f"http://127.0.0.1:5000/recuperar-senha/{usuario[0]}"
            # Exemplo de envio (não envia realmente, apenas simula)
            print(f"Enviar para {email}: Clique para recuperar sua senha: {link}")
            flash("Um link de recuperação foi enviado para seu e-mail.")
            return render_template("recuperar-senha.html")
        else:
            flash("E-mail não encontrado.")
            return render_template("recuperar-senha.html")
        
@app.route("/home", methods=["GET"])
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)

