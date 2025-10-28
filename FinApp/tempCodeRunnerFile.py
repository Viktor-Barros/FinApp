return render_template(
        "consultor.html",
        user_nome=session["user_nome"],
        transacoes=transacoes
    )