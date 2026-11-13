from datetime import datetime, timezone
from backend.database import db


def utc_now():
    return datetime.now(timezone.utc)


SITUACOES_CHAMADO = ["Aberto", "Em andamento", "Resolvido"]


class Chamado(db.Model):
    __tablename__ = "chamados"

    id = db.Column(db.Integer, primary_key=True)
    numero_chamado = db.Column(db.String(30), unique=True, nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey("laboratorios.id"), nullable=False)
    computador_id = db.Column(db.Integer, db.ForeignKey("computadores.id"), nullable=True)
    descricao = db.Column(db.Text, nullable=False)
    situacao = db.Column(db.String(20), default="Aberto", nullable=False)  # Aberto, Em andamento, Resolvido
    responsavel_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    nota_atendimento = db.Column(db.Text, nullable=True)
    data_abertura = db.Column(db.DateTime, default=utc_now, nullable=False)
    data_conclusao = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship("Usuario", back_populates="chamados_abertos", foreign_keys=[usuario_id])
    responsavel = db.relationship("Usuario", back_populates="chamados_atendidos", foreign_keys=[responsavel_id])
    laboratorio = db.relationship("Laboratorio", back_populates="chamados", foreign_keys=[laboratorio_id])
    computador = db.relationship("Computador", back_populates="chamados", foreign_keys=[computador_id])

    def __repr__(self):
        return f"<Chamado {self.numero_chamado} ({self.situacao})>"
