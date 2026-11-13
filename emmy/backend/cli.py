import getpass
import sys
from backend.app import create_app
from backend.database import db
from backend.models.usuario import Usuario
from backend.models.laboratorio import Laboratorio
from backend.models.computador import Computador
from backend.models.reserva import Reserva
from backend.models.chamado import Chamado


def init_db():
    """Cria todas as tabelas no banco de dados SQLite."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print(" Banco de dados inicializado com sucesso!")


def create_admin_interactive():
    """Cria o primeiro administrador de forma segura sem credenciais fixas no código."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("=== LabControl - Inicialização Segura do Administrador ===")
        nome = input("Nome completo do Administrador: ").strip()
        email = input("E-mail corporativo: ").strip()
        username = input("Nome de usuário (login): ").strip()

        if not nome or not email or not username:
            print(" Erro: Todos os campos são obrigatórios.")
            sys.exit(1)

        # Verificar se já existe
        if Usuario.query.filter((Usuario.username == username) | (Usuario.email == email)).first():
            print(" Erro: Já existe um usuário cadastrado com este username ou e-mail.")
            sys.exit(1)

        senha = getpass.getpass("Senha segura (mínimo 6 caracteres): ")
        senha_confirm = getpass.getpass("Confirme a senha: ")

        if senha != senha_confirm:
            print(" Erro: As senhas não conferem.")
            sys.exit(1)

        if len(senha) < 6:
            print(" Erro: A senha deve conter pelo menos 6 caracteres.")
            sys.exit(1)

        admin = Usuario(
            nome=nome,
            email=email,
            username=username,
            perfil="Administrador",
            ativo=True,
        )
        admin.set_senha(senha)
        db.session.add(admin)
        db.session.commit()
        print(f" Administrador '{username}' criado com sucesso e senha protegida por hash!")


def seed_demo_data(admin_password="AdminSecure@2026", professor_password="ProfSecure@2026", ti_password="TISecure@2026"):
    """
    Popula o banco com dados de exemplo claros para demonstração e testes da banca/usuário.
    """
    from datetime import date, time, timedelta, datetime, timezone
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Banco resetado e tabelas criadas.")

        # Criar usuários de demonstração
        admin = Usuario(
            nome="Administrador do Sistema",
            email="admin@labcontrol.escola.br",
            username="admin",
            perfil="Administrador",
            ativo=True,
        )
        admin.set_senha(admin_password)

        prof = Usuario(
            nome="Prof. Carlos Eduardo Silveira",
            email="carlos.silveira@labcontrol.escola.br",
            username="prof.carlos",
            perfil="Professor",
            ativo=True,
        )
        prof.set_senha(professor_password)

        prof2 = Usuario(
            nome="Profa. Mariana Costa Santos",
            email="mariana.costa@labcontrol.escola.br",
            username="profa.mariana",
            perfil="Professor",
            ativo=True,
        )
        prof2.set_senha(professor_password)

        ti = Usuario(
            nome="Lucas Ferreira (Técnico TI)",
            email="lucas.ti@labcontrol.escola.br",
            username="ti.lucas",
            perfil="TI",
            ativo=True,
        )
        ti.set_senha(ti_password)

        db.session.add_all([admin, prof, prof2, ti])
        db.session.commit()
        print("Usuários de teste criados.")

        # Criar Laboratórios
        lab1 = Laboratorio(
            identificador="LAB-01",
            nome="Laboratório de Informática Geral",
            capacidade_maxima=40,
            descricao="Laboratório principal para aulas curriculares e treinamentos."
        )
        lab2 = Laboratorio(
            identificador="LAB-02",
            nome="Laboratório de Redes e Hardware",
            capacidade_maxima=30,
            descricao="Ambiente para práticas de redes de computadores e manutenção."
        )
        lab3 = Laboratorio(
            identificador="LAB-03",
            nome="Laboratório de Robótica e Maker",
            capacidade_maxima=25,
            descricao="Bancadas equipadas com kits de automação e robótica."
        )

        db.session.add_all([lab1, lab2, lab3])
        db.session.commit()
        print("Laboratórios criados.")

        # Criar Computadores para LAB-01 (40 computadores: 35 funcionando, 3 defeito, 2 manutenção)
        pcs_lab1 = []
        for i in range(1, 41):
            if i in [36, 37, 38]:
                estado = "Com defeito"
                obs = "Fonte de alimentação queimada / aguardando troca"
            elif i in [39, 40]:
                estado = "Em manutenção"
                obs = "Reinstalação do sistema operacional e limpeza interna"
            else:
                estado = "Funcionando"
                obs = "Equipamento em perfeito estado de funcionamento"

            pc = Computador(
                identificador=f"PC-L01-{i:02d}",
                hostname=f"lab01-desk{i:02d}",
                laboratorio_id=lab1.id,
                estado=estado,
                observacao=obs,
            )
            pcs_lab1.append(pc)

        # Criar Computadores para LAB-02 (30 computadores: 28 funcionando, 2 com defeito)
        pcs_lab2 = []
        for i in range(1, 31):
            estado = "Com defeito" if i in [29, 30] else "Funcionando"
            obs = "Placa de rede com falha de conexão" if i in [29, 30] else "OK"
            pc = Computador(
                identificador=f"PC-L02-{i:02d}",
                hostname=f"lab02-desk{i:02d}",
                laboratorio_id=lab2.id,
                estado=estado,
                observacao=obs,
            )
            pcs_lab2.append(pc)

        # Criar Computadores para LAB-03 (25 computadores: todos funcionando)
        pcs_lab3 = []
        for i in range(1, 26):
            pc = Computador(
                identificador=f"PC-L03-{i:02d}",
                hostname=f"lab03-desk{i:02d}",
                laboratorio_id=lab3.id,
                estado="Funcionando",
                observacao="Computador pronto para uso de software CAD e robótica",
            )
            pcs_lab3.append(pc)

        db.session.add_all(pcs_lab1 + pcs_lab2 + pcs_lab3)
        db.session.commit()
        print("Computadores cadastrados e vinculados.")

        # Criar Reservas de exemplo
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        depois = hoje + timedelta(days=2)

        res1 = Reserva(
            professor_id=prof.id,
            laboratorio_id=lab1.id,
            turma="3º Ano Informática B",
            quantidade_alunos=32,
            data=amanha,
            horario_inicio=time(8, 0),
            horario_fim=time(10, 0),
            finalidade="Aula prática de Programação Web e Banco de Dados",
            situacao="Confirmada",
        )

        res2 = Reserva(
            professor_id=prof2.id,
            laboratorio_id=lab2.id,
            turma="2º Ano Redes A",
            quantidade_alunos=26,
            data=depois,
            horario_inicio=time(13, 30),
            horario_fim=time(15, 30),
            finalidade="Configuração de switches e roteamento VLAN",
            situacao="Confirmada",
        )

        db.session.add_all([res1, res2])
        db.session.commit()
        print("Reservas de teste criadas.")

        # Criar Chamados de exemplo
        chamado1 = Chamado(
            numero_chamado="CHM-2026-0001",
            usuario_id=prof.id,
            laboratorio_id=lab1.id,
            computador_id=pcs_lab1[35].id,  # PC-L01-36
            descricao="Computador não liga após queda de energia local.",
            situacao="Aberto",
            data_abertura=datetime.now(timezone.utc) - timedelta(hours=5),
        )

        chamado2 = Chamado(
            numero_chamado="CHM-2026-0002",
            usuario_id=prof.id,
            laboratorio_id=lab1.id,
            computador_id=pcs_lab1[38].id,  # PC-L01-39
            descricao="Sistema corrompido em loop de reinicialização.",
            situacao="Em andamento",
            responsavel_id=ti.id,
            nota_atendimento="Iniciada reinstalação da imagem oficial da escola.",
            data_abertura=datetime.now(timezone.utc) - timedelta(hours=12),
        )

        chamado3 = Chamado(
            numero_chamado="CHM-2026-0003",
            usuario_id=prof2.id,
            laboratorio_id=lab2.id,
            computador_id=pcs_lab2[0].id,
            descricao="Teclado com teclas de atalho travadas.",
            situacao="Resolvido",
            responsavel_id=ti.id,
            nota_atendimento="Teclado substituído por novo periférico do estoque.",
            data_abertura=datetime.now(timezone.utc) - timedelta(days=2),
            data_conclusao=datetime.now(timezone.utc) - timedelta(days=1),
        )

        db.session.add_all([chamado1, chamado2, chamado3])
        db.session.commit()
        print("Chamados de exemplo criados.")
        print("\n=== Banco populado com sucesso para demonstração! ===")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init-db":
            init_db()
        elif cmd == "create-admin":
            create_admin_interactive()
        elif cmd == "seed":
            seed_demo_data()
        else:
            print("Comandos disponíveis: init-db, create-admin, seed")
    else:
        init_db()
