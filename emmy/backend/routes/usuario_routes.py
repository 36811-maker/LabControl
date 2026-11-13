from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from backend.database import db
from backend.models.usuario import Usuario
from backend.services.auth_service import role_required, validate_password_strength

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/")
@login_required
@role_required("Administrador")
def index():
    q = request.args.get("q", "").strip()
    perfil = request.args.get("perfil", "").strip()
    status = request.args.get("status", "").strip()

    query = Usuario.query

    if q:
        query = query.filter(
            (Usuario.nome.ilike(f"%{q}%")) |
            (Usuario.email.ilike(f"%{q}%")) |
            (Usuario.username.ilike(f"%{q}%"))
        )

    if perfil and perfil in ["Administrador", "Professor", "TI"]:
        query = query.filter_by(perfil=perfil)

    if status == "ativo":
        query = query.filter_by(ativo=True)
    elif status == "inativo":
        query = query.filter_by(ativo=False)

    usuarios = query.order_by(Usuario.nome.asc()).all()
    return render_template("usuarios.html", usuarios=usuarios, q=q, perfil=perfil, status=status)


@usuario_bp.route("/novo", methods=["POST"])
@login_required
@role_required("Administrador")
def novo():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    username = request.form.get("username", "").strip().lower()
    perfil = request.form.get("perfil", "").strip()
    senha = request.form.get("senha", "")

    if not nome or not email or not username or not perfil or not senha:
        flash("Todos os campos são obrigatórios.", "danger")
        return redirect(url_for("usuarios.index"))

    if perfil not in ["Administrador", "Professor", "TI"]:
        flash("Perfil de usuário inválido.", "danger")
        return redirect(url_for("usuarios.index"))

    valido, msg = validate_password_strength(senha)
    if not valido:
        flash(msg, "danger")
        return redirect(url_for("usuarios.index"))

    if Usuario.query.filter_by(username=username).first():
        flash(f"O nome de usuário '{username}' já está em uso.", "danger")
        return redirect(url_for("usuarios.index"))

    if Usuario.query.filter_by(email=email).first():
        flash(f"O e-mail '{email}' já está em uso.", "danger")
        return redirect(url_for("usuarios.index"))

    usuario = Usuario(
        nome=nome,
        email=email,
        username=username,
        perfil=perfil,
        ativo=True,
    )
    usuario.set_senha(senha)
    db.session.add(usuario)
    db.session.commit()

    flash(f"Usuário '{usuario.nome}' ({usuario.perfil}) cadastrado com sucesso!", "success")
    return redirect(url_for("usuarios.index"))


@usuario_bp.route("/<int:user_id>/editar", methods=["POST"])
@login_required
@role_required("Administrador")
def editar(user_id):
    usuario = Usuario.query.get_or_404(user_id)

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    perfil = request.form.get("perfil", "").strip()
    ativo = request.form.get("ativo") == "1"
    nova_senha = request.form.get("nova_senha", "").strip()

    if not nome or not email or not perfil:
        flash("Nome, e-mail e perfil são campos obrigatórios.", "danger")
        return redirect(url_for("usuarios.index"))

    if perfil not in ["Administrador", "Professor", "TI"]:
        flash("Perfil de usuário inválido.", "danger")
        return redirect(url_for("usuarios.index"))

    # Checar duplicidade de e-mail
    existente = Usuario.query.filter(Usuario.email == email, Usuario.id != user_id).first()
    if existente:
        flash(f"O e-mail '{email}' já pertence a outro usuário.", "danger")
        return redirect(url_for("usuarios.index"))

    # Segurança: não permitir que o próprio usuário conectado se desative ou perca cargo de admin se for o último
    if current_user.id == usuario.id:
        if not ativo:
            flash("Você não pode desativar sua própria conta enquanto estiver conectado.", "warning")
            ativo = True
        if perfil != "Administrador":
            flash("Você não pode alterar seu próprio perfil de Administrador.", "warning")
            perfil = "Administrador"

    # Verificar se restará pelo menos um administrador ativo
    if usuario.perfil == "Administrador" and (perfil != "Administrador" or not ativo):
        total_admins_ativos = Usuario.query.filter_by(perfil="Administrador", ativo=True).count()
        if total_admins_ativos <= 1:
            flash("Operação bloqueada: o sistema precisa manter pelo menos um Administrador ativo.", "danger")
            return redirect(url_for("usuarios.index"))

    usuario.nome = nome
    usuario.email = email
    usuario.perfil = perfil
    usuario.ativo = ativo

    if nova_senha:
        valido, msg = validate_password_strength(nova_senha)
        if not valido:
            flash(msg, "danger")
            return redirect(url_for("usuarios.index"))
        usuario.set_senha(nova_senha)

    db.session.commit()
    flash(f"Dados do usuário '{usuario.nome}' atualizados com sucesso!", "success")
    return redirect(url_for("usuarios.index"))


@usuario_bp.route("/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@role_required("Administrador")
def toggle_status(user_id):
    usuario = Usuario.query.get_or_404(user_id)

    if current_user.id == usuario.id:
        flash("Você não pode desativar seu próprio acesso.", "warning")
        return redirect(url_for("usuarios.index"))

    if usuario.perfil == "Administrador" and usuario.ativo:
        total_admins_ativos = Usuario.query.filter_by(perfil="Administrador", ativo=True).count()
        if total_admins_ativos <= 1:
            flash("Não é permitido desativar o único administrador ativo do sistema.", "danger")
            return redirect(url_for("usuarios.index"))

    usuario.ativo = not usuario.ativo
    db.session.commit()

    estado_str = "ativado" if usuario.ativo else "desativado"
    flash(f"Usuário '{usuario.nome}' foi {estado_str} com sucesso.", "success")
    return redirect(url_for("usuarios.index"))
