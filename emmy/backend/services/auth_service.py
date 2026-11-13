from functools import wraps
import secrets
from flask import session, request, abort, flash, redirect, url_for
from flask_login import current_user
from backend.models.usuario import Usuario


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf():
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        expected = session.get("_csrf_token")
        if not expected or not token or not secrets.compare_digest(token, expected):
            flash("Requisição inválida ou sessão expirada. Tente novamente.", "danger")
            abort(400)


def role_required(*allowed_roles):
    """
    Decorator para verificar se o usuário autenticado possui o perfil necessário.
    Exemplo: @role_required('Administrador', 'TI')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Faça login para acessar esta página.", "warning")
                return redirect(url_for("auth.login"))
            
            if not current_user.ativo:
                flash("Sua conta está desativada. Entre em contato com o suporte.", "danger")
                return redirect(url_for("auth.logout"))

            if current_user.perfil not in allowed_roles:
                flash("Acesso não autorizado para o seu perfil.", "danger")
                return redirect(url_for("dashboard.index"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Valida requisitos mínimos da senha."""
    if len(password) < 6:
        return False, "A senha deve conter no mínimo 6 caracteres."
    return True, ""
