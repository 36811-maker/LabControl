from backend.models.chamado import Chamado
from backend.models.computador import Computador
from backend.database import db


def test_abrir_e_resolver_chamado_ciclo_completo(client, seed_test_data):
    # 1. Professor abre chamado com marcação de defeito no PC
    client.post("/login", data={"identificador": "prof.roberto", "senha": "prof123"})

    with client.application.app_context():
        pc = Computador.query.filter_by(identificador="PC-L01-10").first()
        pc_id = pc.id
        assert pc.estado == "Funcionando"

    resp_abrir = client.post("/chamados/novo", data={
        "laboratorio_id": str(seed_test_data["lab1_id"]),
        "computador_id": str(pc_id),
        "descricao": "Monitor piscando intermitente e desligando.",
        "marcar_defeito": "1",
    }, follow_redirects=True)
    assert resp_abrir.status_code == 200
    assert "aberto com sucesso".encode("utf-8") in resp_abrir.data

    with client.application.app_context():
        # Verifica se o PC foi colocado como "Com defeito"
        pc_atualizado = Computador.query.get(pc_id)
        assert pc_atualizado.estado == "Com defeito"

        # Verifica chamado aberto
        chm = Chamado.query.filter_by(computador_id=pc_id).first()
        assert chm is not None
        assert chm.situacao == "Aberto"
        assert chm.data_conclusao is None
        chm_id = chm.id

    # 2. Técnico de TI assume e atualiza chamado
    client.get("/logout")
    client.post("/login", data={"identificador": "ti.user", "senha": "ti1234"})

    resp_atend = client.post(f"/chamados/{chm_id}/atualizar", data={
        "situacao": "Em andamento",
        "nota_atendimento": "Cabo HDMI trocado, iniciando testes de estabilidade.",
        "pc_estado": "Em manutenção",
    }, follow_redirects=True)
    assert resp_atend.status_code == 200

    with client.application.app_context():
        chm_andamento = Chamado.query.get(chm_id)
        assert chm_andamento.situacao == "Em andamento"
        assert chm_andamento.computador.estado == "Em manutenção"

    # 3. Técnico resolve o chamado e retorna PC para "Funcionando"
    resp_resolv = client.post(f"/chamados/{chm_id}/atualizar", data={
        "situacao": "Resolvido",
        "nota_atendimento": "Concluído com sucesso. Monitor 100% funcional.",
        "pc_estado": "Funcionando",
    }, follow_redirects=True)
    assert resp_resolv.status_code == 200

    with client.application.app_context():
        chm_resolvido = Chamado.query.get(chm_id)
        assert chm_resolvido.situacao == "Resolvido"
        assert chm_resolvido.data_conclusao is not None
        assert chm_resolvido.computador.estado == "Funcionando"
