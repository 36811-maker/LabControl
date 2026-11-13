from backend.models.laboratorio import Laboratorio
from backend.models.computador import Computador
from backend.database import db


def test_lab_metrics_counts(app, seed_test_data):
    with app.app_context():
        lab = Laboratorio.query.get(seed_test_data["lab1_id"])
        assert lab.total_computadores == 40
        assert lab.computadores_funcionando == 35
        assert lab.computadores_defeito == 3
        assert lab.computadores_manutencao == 2


def test_criar_laboratorio_admin(client, seed_test_data):
    client.post("/login", data={"identificador": "admin", "senha": "admin123"})
    response = client.post("/laboratorios/novo", data={
        "identificador": "LAB-09",
        "nome": "Laboratório de Redes Avançadas",
        "capacidade_maxima": "30",
        "descricao": "Roteadores e Switches",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "LAB-09".encode("utf-8") in response.data


def test_bloquear_exclusao_lab_com_computadores(client, seed_test_data):
    client.post("/login", data={"identificador": "admin", "senha": "admin123"})
    lab_id = seed_test_data["lab1_id"]
    response = client.post(f"/laboratorios/{lab_id}/excluir", follow_redirects=True)
    assert response.status_code == 200
    assert "Não é possível excluir o laboratório".encode("utf-8") in response.data

    with client.application.app_context():
        assert Laboratorio.query.get(lab_id) is not None
