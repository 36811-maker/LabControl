from datetime import datetime, timezone
from backend.database import db


def utc_now():
    return datetime.now(timezone.utc)


SITUACOES_RESERVA = ["Confirmada", "Cancelada"]


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey("laboratorios.id"), nullable=False)
    turma = db.Column(db.String(50), nullable=False)
    quantidade_alunos = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Date, nullable=False, index=True)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    finalidade = db.Column(db.Text, nullable=True)
    situacao = db.Column(db.String(20), default="Confirmada", nullable=False)  # Confirmada, Cancelada
    criado_em = db.Column(db.DateTime, default=utc_now, nullable=False)

    professor = db.relationship("Usuario", back_populates="reservas", foreign_keys=[professor_id])
    laboratorio = db.relationship("Laboratorio", back_populates="reservas", foreign_keys=[laboratorio_id])

    def __repr__(self):
        return f"<Reserva Lab:{self.laboratorio_id} Data:{self.data} ({self.situacao})>"
