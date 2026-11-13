from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database import db


def utc_now():
    return datetime.now(timezone.utc)


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)  # Administrador, Professor, TI
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=utc_now, nullable=False)

    reservas = db.relationship("Reserva", back_populates="professor", foreign_keys="Reserva.professor_id")
    chamados_abertos = db.relationship("Chamado", back_populates="usuario", foreign_keys="Chamado.usuario_id")
    chamados_atendidos = db.relationship("Chamado", back_populates="responsavel", foreign_keys="Chamado.responsavel_id")

    def set_senha(self, senha: str):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self) -> bool:
        return self.perfil == "Administrador"

    @property
    def is_professor(self) -> bool:
        return self.perfil == "Professor"

    @property
    def is_ti(self) -> bool:
        return self.perfil == "TI"

    def __repr__(self):
        return f"<Usuario {self.username} ({self.perfil})>"
