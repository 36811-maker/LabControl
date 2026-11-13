from datetime import datetime, timezone
from backend.database import db


def utc_now():
    return datetime.now(timezone.utc)


class Laboratorio(db.Model):
    __tablename__ = "laboratorios"

    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(100), nullable=False)
    capacidade_maxima = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=utc_now, nullable=False)

    computadores = db.relationship("Computador", back_populates="laboratorio", lazy="dynamic")
    reservas = db.relationship("Reserva", back_populates="laboratorio", lazy="dynamic")
    chamados = db.relationship("Chamado", back_populates="laboratorio", lazy="dynamic")

    @property
    def total_computadores(self) -> int:
        return self.computadores.count()

    @property
    def computadores_funcionando(self) -> int:
        return self.computadores.filter_by(estado="Funcionando").count()

    @property
    def computadores_defeito(self) -> int:
        return self.computadores.filter_by(estado="Com defeito").count()

    @property
    def computadores_manutencao(self) -> int:
        return self.computadores.filter_by(estado="Em manutenção").count()

    def __repr__(self):
        return f"<Laboratorio {self.identificador} - {self.nome}>"
