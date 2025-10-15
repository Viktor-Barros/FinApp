from flask import Flask, request, render_template, flash, redirect, url_for, session
from db import get_connection

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"

@app.route("/")
def index():
    return render_template("index.html")

# ----------------- Cadastro de Usuário -----------------
@app.route("/cadastro", methods=["GET"])
def cadastro_form():
    return render_template("cadastro.html")

@app.route("/cadastro", methods=["POST"])
def cadastro():
    conn = get_connection()
    cursor = conn.cursor()

    # Captura os campos do formulário
    nome = request.form.get("nome")
    data_nasc = request.form.get("dataNasc")
    cpf = request.form.get("cpf")
    email = request.form.get("emailUsuario")
    senha = request.form.get("senhaUsuario")
    renda = float(request.form.get("renda", 0))
    profissao = request.form.get("profissao")
    codigo = int(request.form.get("codigo", 0))

    # Verifica se o consultor existe
    id_consultor = codigo if codigo != 0 else None
    if id_consultor:
        cursor.execute("SELECT id_consultor FROM TB_Consultor WHERE id_consultor = ?", (id_consultor,))
        if cursor.fetchone() is None:
            id_consultor = None

    # Inserção na tabela TB_Usuario
    sql = """
        INSERT INTO TB_Usuario
        (id_consultor, nome, email, senha, data_nasc, profissao, cpf, renda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (id_consultor, nome, email, senha, data_nasc, profissao, cpf, renda))
    conn.commit()
    id_usuario = cursor.lastrowid

    cursor.close()
    conn.close()
    flash(f"Usuário {nome} cadastrado com sucesso! ID: {id_usuario}")
    return redirect(url_for("index"))

# ----------------- Cadastro de Consultor -----------------
@app.route("/cadastro-consultor", methods=["POST"])
def cadastro_consultor():
    conn = get_connection()
    cursor = conn.cursor()

    responsavel = request.form.get("responsavel")
    empresa = request.form.get("empresa")
    cnpj = request.form.get("cnpj")
    ramo = request.form.get("ramo")
    email = request.form.get("emailConsultor")
    senha = request.form.get("senhaConsultor")

    # Inserção na tabela TB_Consultor
    sql = """
        INSERT INTO TB_Consultor
        (nome, email, senha, nome_empresa, cnpj, ramo_empresa)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (responsavel, email, senha, empresa, cnpj, ramo))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f"Consultor {responsavel} cadastrado com sucesso!")
    return redirect(url_for("index"))

# ----------------- Login -----------------
@app.route("/login", methods=["GET", "POST"])
def login_form():
    if request.method == "GET":
        return render_template("index.html")
    
    # POST - autenticação
    email = request.form.get("email")
    senha = request.form.get("senha")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nome FROM TB_Usuario WHERE email = ? AND senha = ?", (email, senha))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if usuario:
        # Salva dados do usuário na sessão
        session['user_id'] = usuario[0]
        session['user_nome'] = usuario[1]
        return redirect(url_for("home"))
    else:
        flash("Usuário ou senha incorretos.")
        return redirect(url_for("login_form"))

# ----------------- Recuperar senha -----------------
@app.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    if request.method == "GET":
        return render_template("recuperar-senha.html")
    else:
        email = request.form.get("email")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM TB_Usuario WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario:
            link = f"http://127.0.0.1:5000/recuperar-senha/{usuario[0]}"
            print(f"Enviar para {email}: Clique para recuperar sua senha: {link}")
            flash("Um link de recuperação foi enviado para seu e-mail.")
        else:
            flash("E-mail não encontrado.")
        return render_template("recuperar-senha.html")

# ----------------- Home -----------------
@app.route("/home", methods=["GET"])
def home():
    if 'user_id' not in session:
        flash("Faça login para acessar a página Home.")
        return redirect(url_for("login_form"))
    
    nome = session.get('user_nome')
    return render_template("home.html", nome=nome)

# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso.")
    return redirect(url_for("login_form"))

if __name__ == "__main__":
    app.run(debug=True)
