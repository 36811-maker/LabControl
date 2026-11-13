from datetime import datetime, timezone
from backend.database import db


def utc_now():
    return datetime.now(timezone.utc)


ESTADOS_COMPUTADOR = ["Funcionando", "Com defeito", "Em manutenção"]


class Computador(db.Model):
    __tablename__ = "computadores"

    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(50), unique=True, nullable=False, index=True)
    hostname = db.Column(db.String(100), nullable=False)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey("laboratorios.id"), nullable=False)
    estado = db.Column(db.String(30), default="Funcionando", nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=utc_now, nullable=False)

    laboratorio = db.relationship("Laboratorio", back_populates="computadores")
    chamados = db.relationship("Chamado", back_populates="computador", lazy="dynamic")

    def __repr__(self):
        return f"<Computador {self.identificador} ({self.estado})>"
