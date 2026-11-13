import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from backend.config import Config
from backend.database import db
from backend.models.usuario import Usuario
from backend.services.auth_service import generate_csrf_token, validate_csrf

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = str(BASE_DIR / "frontend" / "templates")
STATIC_DIR = str(BASE_DIR / "frontend" / "static")

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
        static_url_path="/static",
    )
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    # Proteção CSRF
    @app.before_request
    def check_csrf():
        # Ignora verificação CSRF em testes unitários se desabilitado
        if app.config.get("WTF_CSRF_ENABLED", True) is False:
            return
        validate_csrf()

    # Context processors para templates
    @app.context_processor
    def inject_context():
        return {
            "csrf_token": generate_csrf_token,
            "current_year": datetime.now().year,
        }

    # Registrar blueprints
    from backend.routes.auth_routes import auth_bp
    from backend.routes.dashboard_routes import dashboard_bp
    from backend.routes.laboratorio_routes import lab_bp
    from backend.routes.computador_routes import pc_bp
    from backend.routes.reserva_routes import reserva_bp
    from backend.routes.chamado_routes import chamado_bp
    from backend.routes.usuario_routes import usuario_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(lab_bp, url_prefix="/laboratorios")
    app.register_blueprint(pc_bp, url_prefix="/computadores")
    app.register_blueprint(reserva_bp, url_prefix="/reservas")
    app.register_blueprint(chamado_bp, url_prefix="/chamados")
    app.register_blueprint(usuario_bp, url_prefix="/usuarios")

    # Tratamento de erros
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500

    return app
