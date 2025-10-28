from flask import Flask, request, render_template, flash, redirect, url_for, session, jsonify
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

    # Verifica na tabela de usuários
    cursor.execute("SELECT id_usuario, nome FROM TB_Usuario WHERE email = ? AND senha = ?", (email, senha))
    usuario = cursor.fetchone()

    if usuario:
        session["user_id"] = usuario[0]
        session["user_nome"] = usuario[1]
        session["user_tipo"] = "usuario"

        cursor.close()
        conn.close()

        # Redireciona para /home (muda o caminho da URL)
        return redirect(url_for("home"))

    # Verifica na tabela de consultores
    cursor.execute("SELECT id_consultor, nome FROM TB_Consultor WHERE email = ? AND senha = ?", (email, senha))
    consultor = cursor.fetchone()

    cursor.close()
    conn.close()

    if consultor:
        session["user_id"] = consultor[0]
        session["user_nome"] = consultor[1]
        session["user_tipo"] = "consultor"

        # Redireciona para /consultor (muda o caminho da URL)
        return redirect(url_for("consultor"))

    # Se não achou em nenhuma das tabelas
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

# ----------------- Consultor ----------------

@app.route('/consultor')
def consultor():
    if 'user_id' not in session:
        return redirect(url_for('login_form'))

    conn = get_connection()
    cursor = conn.cursor()

    # Busca todas as transações junto com o nome dos usuários
    cursor.execute("""
        SELECT u.nome, t.tipo, t.categoria, t.valor
        FROM TB_Transacao t
        JOIN TB_Usuario u ON t.id_usuario = u.id_usuario
    """)
    transacoes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("consultor.html", transacoes=transacoes)

# ----------------- Home -----------------

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login_form'))  # redireciona se não estiver logado

    id_usuario = session['user_id']

    conn = get_connection()
    cursor = conn.cursor()

    # Pega todas as transações do usuário logado
    cursor.execute("SELECT tipo, categoria, valor FROM TB_Transacao WHERE id_usuario = ?", (id_usuario,))
    transacoes = cursor.fetchall()

    cursor.close()
    conn.close()

    # Calcula totais
    total_receitas = float(sum(t[2] for t in transacoes if t[0] == 'receita'))
    total_despesas = float(sum(t[2] for t in transacoes if t[0] == 'gasto'))
    saldo_disponivel = total_receitas - total_despesas

    # Para gráfico por categoria (opcional)
    categorias = sorted(list(set([t[1] for t in transacoes])))
    dados_receita = [sum(t[2] for t in transacoes if t[1] == c and t[0] == 'receita') for c in categorias]
    dados_despesa = [sum(t[2] for t in transacoes if t[1] == c and t[0] == 'gasto') for c in categorias]
    dados_saldo = [r - d for r, d in zip(dados_receita, dados_despesa)]

    return render_template(
        "home.html",
        user_nome=session.get("user_nome", "Usuário"),
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo_disponivel=saldo_disponivel,
        categorias=categorias,
        dados_receita=dados_receita,
        dados_despesa=dados_despesa,
        dados_saldo=dados_saldo
    )


# ----------------- Transações -----------------

@app.route("/transacoes", methods=["GET", "POST"])
def transacoes():
    # Verifica se o usuário está logado
    if "user_id" not in session:
        flash("Faça login para acessar as transações.")
        return redirect(url_for("login_form"))

    conn = get_connection()
    cursor = conn.cursor()

    # --- POST: salvar nova transação via AJAX ---
    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"status": "erro", "mensagem": "Dados inválidos"}), 400

        descricao = data.get("descricao")
        valor = data.get("valor")
        tipo = data.get("tipo")
        categoria = data.get("categoria")
        data_transacao = data.get("data")
        user_id = session["user_id"]

        try:
            cursor.execute("""
                INSERT INTO TB_Transacao (descricao, tipo, categoria, valor, data_transacao, id_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (descricao, tipo, categoria, float(valor), data_transacao, user_id))
            conn.commit()

            # Retorna JSON para o JS atualizar a tela
            return jsonify({
                "status": "ok",
                "transacao": {
                    "descricao": descricao,
                    "valor": float(valor),
                    "tipo": tipo,
                    "categoria": categoria,
                    "data": data_transacao
                }
            })

        except Exception as e:
            conn.rollback()
            return jsonify({"status": "erro", "mensagem": str(e)}), 500

        finally:
            cursor.close()
            conn.close()

    # --- GET: listar transações ---
    try:
        cursor.execute("""
            SELECT descricao, tipo, categoria, valor, data_transacao
            FROM TB_Transacao
            WHERE id_usuario = ?
            ORDER BY data_transacao DESC
        """, (session["user_id"],))
        transacoes = cursor.fetchall()

        total_receita = sum(t[3] for t in transacoes if t[1] == "receita")
        total_gasto = sum(t[3] for t in transacoes if t[1] == "gasto")
        total_investimento = sum(t[3] for t in transacoes if t[1] == "investimento")

    except Exception as e:
        flash(f"Erro ao carregar transações: {e}")
        transacoes = []
        total_receita = total_gasto = total_investimento = 0

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "transacoes.html",
        transacoes=transacoes,
        total_receita=total_receita,
        total_gasto=total_gasto,
        total_investimento=total_investimento
    )

if __name__ == "__main__":
    app.run(debug=True)


# ----------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso.")
    return redirect(url_for("login_form"))

if __name__ == "__main__":
    app.run(debug=True)

