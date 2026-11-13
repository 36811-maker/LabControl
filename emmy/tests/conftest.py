import pytest
from datetime import date, time, timedelta, datetime, timezone
from backend.app import create_app
from backend.config import TestConfig
from backend.database import db
from backend.models.usuario import Usuario
from backend.models.laboratorio import Laboratorio
from backend.models.computador import Computador
from backend.models.reserva import Reserva
from backend.models.chamado import Chamado


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def seed_test_data(app):
    with app.app_context():
        # Usuários
        admin = Usuario(
            nome="Admin Teste",
            email="admin@teste.com",
            username="admin",
            perfil="Administrador",
            ativo=True,
        )
        admin.set_senha("admin123")

        prof1 = Usuario(
            nome="Prof Roberto",
            email="roberto@teste.com",
            username="prof.roberto",
            perfil="Professor",
            ativo=True,
        )
        prof1.set_senha("prof123")

        prof2 = Usuario(
            nome="Profa Ana",
            email="ana@teste.com",
            username="profa.ana",
            perfil="Professor",
            ativo=True,
        )
        prof2.set_senha("prof123")

        ti = Usuario(
            nome="Tecnico TI",
            email="ti@teste.com",
            username="ti.user",
            perfil="TI",
            ativo=True,
        )
        ti.set_senha("ti1234")

        inativo = Usuario(
            nome="Usuario Inativo",
            email="inativo@teste.com",
            username="inativo",
            perfil="Professor",
            ativo=False,
        )
        inativo.set_senha("inativo123")

        db.session.add_all([admin, prof1, prof2, ti, inativo])
        db.session.commit()

        # Laboratório 01 (Capacidade: 40)
        lab1 = Laboratorio(
            identificador="LAB-01",
            nome="Lab Teste 1",
            capacidade_maxima=40,
            descricao="Laboratório de teste 1"
        )
        # Laboratório 02 (Capacidade: 20)
        lab2 = Laboratorio(
            identificador="LAB-02",
            nome="Lab Teste 2",
            capacidade_maxima=20,
            descricao="Laboratório de teste 2"
        )
        db.session.add_all([lab1, lab2])
        db.session.commit()

        # Computadores para LAB-01: 35 Funcionando, 3 Defeito, 2 Manutenção (Total: 40)
        pcs = []
        for i in range(1, 41):
            if i in [36, 37, 38]:
                est = "Com defeito"
            elif i in [39, 40]:
                est = "Em manutenção"
            else:
                est = "Funcionando"
            pc = Computador(
                identificador=f"PC-L01-{i:02d}",
                hostname=f"l01-pc{i:02d}",
                laboratorio_id=lab1.id,
                estado=est,
            )
            pcs.append(pc)

        db.session.add_all(pcs)
        db.session.commit()

        return {
            "admin_id": admin.id,
            "prof1_id": prof1.id,
            "prof2_id": prof2.id,
            "ti_id": ti.id,
            "inativo_id": inativo.id,
            "lab1_id": lab1.id,
            "lab2_id": lab2.id,
        }
