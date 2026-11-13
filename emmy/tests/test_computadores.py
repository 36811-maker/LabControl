from backend.models.computador import Computador
from backend.models.chamado import Chamado
from backend.database import db


def test_cadastrar_computador_ti(client, seed_test_data):
    client.post("/login", data={"identificador": "ti.user", "senha": "ti1234"})
    response = client.post("/computadores/novo", data={
        "identificador": "PC-L02-01",
        "hostname": "l02-pc01",
        "laboratorio_id": str(seed_test_data["lab2_id"]),
        "estado": "Funcionando",
        "observacao": "Recém instalado",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "PC-L02-01".encode("utf-8") in response.data


def test_atualizar_estado_computador(client, seed_test_data):
    client.post("/login", data={"identificador": "ti.user", "senha": "ti1234"})
    with client.application.app_context():
        pc = Computador.query.filter_by(identificador="PC-L01-01").first()
        pc_id = pc.id

    response = client.post(f"/computadores/{pc_id}/atualizar-estado", data={
        "estado": "Com defeito",
        "observacao": "Cooler travado",
    }, follow_redirects=True)
    assert response.status_code == 200

    with client.application.app_context():
        pc_atualizado = Computador.query.get(pc_id)
        assert pc_atualizado.estado == "Com defeito"
        assert pc_atualizado.observacao == "Cooler travado"


def test_bloquear_exclusao_computador_com_chamado_aberto(client, seed_test_data):
    client.post("/login", data={"identificador": "ti.user", "senha": "ti1234"})
    with client.application.app_context():
        pc = Computador.query.filter_by(identificador="PC-L01-02").first()
        pc_id = pc.id
        # Cria chamado aberto vinculado
        chm = Chamado(
            numero_chamado="CHM-TEST-01",
            usuario_id=seed_test_data["prof1_id"],
            laboratorio_id=seed_test_data["lab1_id"],
            computador_id=pc_id,
            descricao="Sem vídeo",
            situacao="Aberto",
        )
        db.session.add(chm)
        db.session.commit()

    # Tenta excluir o computador
    response = client.post(f"/computadores/{pc_id}/excluir", follow_redirects=True)
    assert response.status_code == 200
    assert "Não é possível excluir o computador".encode("utf-8") in response.data
