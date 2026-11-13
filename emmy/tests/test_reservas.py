from datetime import date, time, timedelta
from backend.models.reserva import Reserva
from backend.services.reserva_service import validar_reserva
from backend.database import db


def test_validacao_regras_reserva(app, seed_test_data):
    with app.app_context():
        amanha = date.today() + timedelta(days=1)
        ontem = date.today() - timedelta(days=1)
        lab1_id = seed_test_data["lab1_id"]
        lab2_id = seed_test_data["lab2_id"]

        # 1. Laboratório inexistente
        valido, msg = validar_reserva(9999, amanha, time(8, 0), time(10, 0), 20)
        assert not valido
        assert "não foi encontrado" in msg

        # 6. Quantidade de alunos zero ou negativa
        valido, msg = validar_reserva(lab1_id, amanha, time(8, 0), time(10, 0), 0)
        assert not valido
        assert "maior que zero" in msg

        valido, msg = validar_reserva(lab1_id, amanha, time(8, 0), time(10, 0), -5)
        assert not valido

        # 7. Data no passado
        valido, msg = validar_reserva(lab1_id, ontem, time(8, 0), time(10, 0), 20)
        assert not valido
        assert "no passado" in msg

        # 5. Horários inválidos (início >= fim)
        valido, msg = validar_reserva(lab1_id, amanha, time(11, 0), time(10, 0), 20)
        assert not valido
        assert "estritamente anterior" in msg

        valido, msg = validar_reserva(lab1_id, amanha, time(10, 0), time(10, 0), 20)
        assert not valido

        # 2. Capacidade máxima excedida (LAB-02 tem capacidade 20)
        valido, msg = validar_reserva(lab2_id, amanha, time(8, 0), time(10, 0), 25)
        assert not valido
        assert "capacidade máxima" in msg.lower()

        # 3. Quantidade de computadores funcionando (LAB-01 tem 40 capacidade, mas só 35 funcionando)
        # Solicitar 38 computadores deve ser impedido!
        valido, msg = validar_reserva(lab1_id, amanha, time(8, 0), time(10, 0), 38)
        assert not valido
        assert "35 computadores funcionando" in msg

        # Solicitar 32 computadores deve ser permitido!
        valido, msg = validar_reserva(lab1_id, amanha, time(8, 0), time(10, 0), 32)
        assert valido
        assert msg == ""


def test_conflito_de_horarios_sobreposicao(client, seed_test_data):
    # Logar como Prof Roberto e criar primeira reserva das 08:00 às 10:00
    client.post("/login", data={"identificador": "prof.roberto", "senha": "prof123"})
    amanha = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    lab1_id = str(seed_test_data["lab1_id"])

    res1 = client.post("/reservas/nova", data={
        "laboratorio_id": lab1_id,
        "turma": "Turma A",
        "quantidade_alunos": "30",
        "data": amanha,
        "horario_inicio": "08:00",
        "horario_fim": "10:00",
        "finalidade": "Aula prática",
    }, follow_redirects=True)
    assert res1.status_code == 200
    assert "confirmada com sucesso".encode("utf-8") in res1.data

    # Logar como Profa Ana e tentar reservar com conflito:
    # 09:00 às 11:00 (sobrepõe parcialmente)
    client.get("/logout")
    client.post("/login", data={"identificador": "profa.ana", "senha": "prof123"})

    res_conflito = client.post("/reservas/nova", data={
        "laboratorio_id": lab1_id,
        "turma": "Turma B",
        "quantidade_alunos": "25",
        "data": amanha,
        "horario_inicio": "09:00",
        "horario_fim": "11:00",
        "finalidade": "Conflito",
    }, follow_redirects=True)
    assert res_conflito.status_code == 200
    assert "Conflito de horário".encode("utf-8") in res_conflito.data

    # Horário posterior livre (10:00 às 12:00) deve passar sem conflito
    res_livre = client.post("/reservas/nova", data={
        "laboratorio_id": lab1_id,
        "turma": "Turma C",
        "quantidade_alunos": "25",
        "data": amanha,
        "horario_inicio": "10:00",
        "horario_fim": "12:00",
        "finalidade": "Horário Livre",
    }, follow_redirects=True)
    assert res_livre.status_code == 200
    assert "confirmada com sucesso".encode("utf-8") in res_livre.data


def test_permissao_cancelamento_reserva(client, seed_test_data):
    # Prof Roberto cria reserva
    client.post("/login", data={"identificador": "prof.roberto", "senha": "prof123"})
    amanha = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    lab1_id = str(seed_test_data["lab1_id"])

    client.post("/reservas/nova", data={
        "laboratorio_id": lab1_id,
        "turma": "Turma Teste",
        "quantidade_alunos": "20",
        "data": amanha,
        "horario_inicio": "14:00",
        "horario_fim": "16:00",
    })

    with client.application.app_context():
        reserva = Reserva.query.filter_by(turma="Turma Teste").first()
        res_id = reserva.id

    # Profa Ana tenta cancelar reserva de Roberto -> DEVE SER BLOQUEADA
    client.get("/logout")
    client.post("/login", data={"identificador": "profa.ana", "senha": "prof123"})
    resp_bloq = client.post(f"/reservas/{res_id}/cancelar", follow_redirects=True)
    assert "Você não tem permissão para cancelar uma reserva pertencente a outro professor".encode("utf-8") in resp_bloq.data

    # Admin tenta cancelar reserva de Roberto -> DEVE TER SUCESSO
    client.get("/logout")
    client.post("/login", data={"identificador": "admin", "senha": "admin123"})
    resp_ok = client.post(f"/reservas/{res_id}/cancelar", follow_redirects=True)
    assert f"Reserva #{res_id} cancelada com sucesso".encode("utf-8") in resp_ok.data
