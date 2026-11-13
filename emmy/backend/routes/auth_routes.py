from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from backend.database import db
from backend.models.usuario import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    # Verifica se existe pelo menos um usuário no sistema; se não existir, orienta sobre o primeiro acesso
    total_usuarios = Usuario.query.count()

    if request.method == "POST":
        identificador = request.form.get("identificador", "").strip()
        senha = request.form.get("senha", "")
        lembrar = bool(request.form.get("lembrar"))

        if not identificador or not senha:
            flash("Preencha todos os campos para entrar no sistema.", "danger")
            return render_template("login.html", total_usuarios=total_usuarios, identificador=identificador)

        # Busca por username ou por e-mail
        usuario = Usuario.query.filter(
            (Usuario.username == identificador) | (Usuario.email == identificador)
        ).first()

        if not usuario or not usuario.check_senha(senha):
            flash("Usuário ou senha incorretos. Verifique suas credenciais.", "danger")
            return render_template("login.html", total_usuarios=total_usuarios, identificador=identificador)

        if not usuario.ativo:
            flash("Esta conta está desativada. Solicite acesso ao administrador.", "danger")
            return render_template("login.html", total_usuarios=total_usuarios, identificador=identificador)

        login_user(usuario, remember=lembrar)
        flash(f"Bem-vindo(a), {usuario.nome}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

    return render_template("login.html", total_usuarios=total_usuarios)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/setup-inicial", methods=["GET", "POST"])
def setup_inicial():
    """Permite inicializar o primeiro administrador se o banco estiver completamente vazio."""
    if Usuario.query.count() > 0:
        flash("O sistema já possui usuários cadastrados. Acesso inicial bloqueado.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        if not nome or not email or not username or not senha:
            flash("Todos os campos são obrigatórios.", "danger")
            return render_template("setup.html")

        if len(senha) < 6:
            flash("A senha deve ter no mínimo 6 caracteres.", "danger")
            return render_template("setup.html")

        if senha != confirmacao:
            flash("As senhas não coincidem.", "danger")
            return render_template("setup.html")

        admin = Usuario(
            nome=nome,
            email=email,
            username=username,
            perfil="Administrador",
            ativo=True
        )
        admin.set_senha(senha)
        db.session.add(admin)
        db.session.commit()

        flash("Primeiro administrador criado com sucesso! Faça login com suas novas credenciais.", "success")
        return redirect(url_for("auth.login"))

    return render_template("setup.html")
