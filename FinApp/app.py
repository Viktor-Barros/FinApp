from flask import Flask, request, render_template, flash, redirect, url_for, session, jsonify, send_file
from db import get_connection
import io
import csv

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

        # Redireciona para /home 
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

        # CORREÇÃO: Redireciona para a função 'consultor_dashboard'
        return redirect(url_for("consultor_dashboard"))

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

# ----------------- Consultor -----------------

@app.route('/consultor')
def consultor_dashboard():
    # CORREÇÃO: Usar 'user_id' que contém o ID do consultor logado
    if session.get('user_tipo') != "consultor" and 'user_id' not in session:
        flash("Acesso restrito a consultores.")
        return redirect(url_for('login_form'))

    # Se estiver logado, usa o user_id da sessão, com fallback 1 se necessário
    consultor_id = session.get('user_id', 1) 
    
    conn = get_connection()
    cursor = conn.cursor()

    # === TOTAL DE CLIENTES DO CONSULTOR ===
    cursor.execute("""
        SELECT COUNT(*) 
        FROM TB_usuario
        WHERE id_consultor = ?
    """, (consultor_id,))
    total_clientes = cursor.fetchone()[0]

    # === RECEITA TOTAL (DAS TRANSAÇÕES DOS CLIENTES) ===
    cursor.execute("""
        SELECT IFNULL(SUM(t.valor), 0)
        FROM TB_Transacao t
        JOIN TB_usuario u ON t.id_usuario = u.id_usuario
        WHERE t.tipo = 'receita' AND u.id_consultor = ?
    """, (consultor_id,))
    receita_total = float(cursor.fetchone()[0])

    # === GASTOS TOTAIS (DAS TRANSAÇÕES DOS CLIENTES) ===
    cursor.execute("""
        SELECT IFNULL(SUM(t.valor), 0)
        FROM TB_Transacao t
        JOIN TB_usuario u ON t.id_usuario = u.id_usuario
        WHERE t.tipo = 'gasto' AND u.id_consultor = ?
    """, (consultor_id,))
    gastos_total = float(cursor.fetchone()[0])

    # === LISTA DE CLIENTES COM SALDO ===
    cursor.execute("""
        SELECT 
            u.id_usuario,
            u.nome,
            u.renda,
            IFNULL((SELECT SUM(t.valor) 
                    FROM TB_Transacao t 
                    WHERE t.tipo='gasto' AND t.id_usuario=u.id_usuario), 0) AS gastos,
            u.renda - IFNULL((SELECT SUM(t.valor) 
                              FROM TB_Transacao t 
                              WHERE t.tipo='gasto' AND t.id_usuario=u.id_usuario), 0) AS saldo
        FROM TB_usuario u
        WHERE u.id_consultor = ?
    """, (consultor_id,))
    clientes = cursor.fetchall()  # lista de tuplas: (id_usuario, nome, renda, gastos, saldo)

    # === NOME DO CONSULTOR ===
    cursor.execute("""
        SELECT nome 
        FROM TB_consultor 
        WHERE id_consultor = ?
    """, (consultor_id,))
    row = cursor.fetchone()
    user_nome = row[0] if row else "Consultor"

    conn.close()

    return render_template(
        'consultor.html',
        user_nome=user_nome,
        total_clientes=total_clientes,
        receita_total=receita_total,
        gastos_total=gastos_total,
        clientes=clientes
    )
# ----------------- Download -----------------

@app.route('/download_clientes')
def download_clientes():
    # CORREÇÃO: Usar 'user_id'
    consultor_id = session.get('user_id', 1) 
    conn = get_connection()
    cursor = conn.cursor()

    # Pega os clientes do consultor
    cursor.execute("""
        SELECT nome, renda, 
        (SELECT IFNULL(SUM(valor),0) FROM TB_Transacao WHERE id_usuario = TB_usuario.id_usuario AND tipo='gasto') AS gastos
        FROM TB_usuario
        WHERE id_consultor = ?
    """, (consultor_id,))
    clientes = cursor.fetchall()
    conn.close()

    # Cria o CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'Salário', 'Despesa', 'Saldo'])
    
    for c in clientes:
        nome = c[0]
        renda = float(c[1] or 0)
        gastos = float(c[2] or 0)
        saldo = renda - gastos
        writer.writerow([nome, f'{renda:.2f}', f'{gastos:.2f}', f'{saldo:.2f}'])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='clientes.csv'
    )

# ----------------- Home -----------------

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login_form')) 

    id_usuario = session['user_id']

    conn = get_connection()
    cursor = conn.cursor()

    # Pega todas as transações do usuário logado
    cursor.execute("SELECT tipo, categoria, valor FROM TB_Transacao WHERE id_usuario = ?", (id_usuario,))
    transacoes = cursor.fetchall()
    
    # === NOVO: Pega todas as metas do usuário logado ===
    # Colunas: id, nome, valor_alvo, valor_atual, data_final, descricao
    cursor.execute("SELECT nome, valor_alvo, valor_atual, data_final FROM TB_Metas WHERE id_usuario = ?", (id_usuario,))
    metas_usuario = cursor.fetchall()

    # Calcula totais
    total_receitas = float(sum(t[2] for t in transacoes if t[0] == 'receita'))
    total_despesas = float(sum(t[2] for t in transacoes if t[0] == 'gasto'))
    saldo_disponivel = total_receitas - total_despesas

    # Para gráfico por categoria (opcional)
    categorias = sorted(list(set([t[1] for t in transacoes])))
    dados_receita = [sum(t[2] for t in transacoes if t[1] == c and t[0] == 'receita') for c in categorias]
    dados_despesa = [sum(t[2] for t in transacoes if t[1] == c and t[0] == 'gasto') for c in categorias]
    dados_saldo = [r - d for r, d in zip(dados_receita, dados_despesa)]

    cursor.close()
    conn.close()
    
    return render_template(
        "home.html",
        user_nome=session.get("user_nome", "Usuário"),
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo_disponivel=saldo_disponivel,
        categorias=categorias,
        dados_receita=dados_receita,
        dados_despesa=dados_despesa,
        dados_saldo=dados_saldo,
        # === NOVO: Passa as metas para o template ===
        metas=metas_usuario 
    )

#---------------------- Metas ----------------------
@app.route('/salvar_meta', methods=['POST'])
def salvar_meta():
    if 'user_id' not in session:
        # Retorna um erro JSON se o usuário não estiver logado
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    id_usuario = session['user_id']
    
    # 1. Tenta receber os dados como JSON
    data = request.get_json(silent=True)
    
    # 2. Se JSON falhar (porque o front-end pode enviar FormData), usa request.form
    if not data:
        data = request.form

    try:
        nome = data['nome']
        valor = float(data['valor'])
        data_final = data['data_final']
        descricao = data.get('descricao', '') # A descrição é opcional
        
        # O campo 'valor_atual' pode ser inicializado como 0.00
        valor_atual = 0.00 

        conn = get_connection()
        cursor = conn.cursor()

        # Insere a nova meta no banco de dados (ajuste o nome da tabela e colunas conforme seu DB)
        # ASSUME: TB_Metas(id_usuario, nome, valor_alvo, valor_atual, data_final, descricao)
        cursor.execute("""
            INSERT INTO TB_Metas (id_usuario, nome, valor_alvo, valor_atual, data_final, descricao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_usuario, nome, valor, valor_atual, data_final, descricao))
        
        conn.commit()
        cursor.close()
        conn.close()

        # Retorna uma resposta de sucesso para o front-end
        return jsonify({'success': True, 'message': 'Meta salva com sucesso!'}), 200

    except KeyError:
        # Se algum campo obrigatório estiver faltando
        return jsonify({'success': False, 'message': 'Dados de meta incompletos'}), 400
    except ValueError:
        # Se o valor não for um número válido
        return jsonify({'success': False, 'message': 'Valor inválido'}), 400
    except Exception as e:
        # Erro genérico do DB ou servidor
        print(f"Erro ao salvar meta: {e}")
        return jsonify({'success': False, 'message': f'Erro interno: {e}'}), 500

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


# ----------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso.")
    return redirect(url_for("index")) # Redirecionar para index, que mostra o login

if __name__ == "__main__":
    app.run(debug=True)