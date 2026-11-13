from datetime import date, datetime, timezone
from backend.models.laboratorio import Laboratorio
from backend.models.computador import Computador
from backend.models.reserva import Reserva
from backend.models.chamado import Chamado
from backend.models.usuario import Usuario


def get_dashboard_metrics(user):
    hoje = date.today()

    total_labs = Laboratorio.query.count()
    total_computadores = Computador.query.count()
    pcs_funcionando = Computador.query.filter_by(estado="Funcionando").count()
    pcs_defeito = Computador.query.filter_by(estado="Com defeito").count()
    pcs_manutencao = Computador.query.filter_by(estado="Em manutenção").count()

    # Reservas futuras ou de hoje confirmadas
    reservas_futuras_query = Reserva.query.filter(
        Reserva.data >= hoje,
        Reserva.situacao == "Confirmada"
    )

    # Chamados gerais
    chamados_abertos = Chamado.query.filter_by(situacao="Aberto").count()
    chamados_em_andamento = Chamado.query.filter_by(situacao="Em andamento").count()
    chamados_resolvidos = Chamado.query.filter_by(situacao="Resolvido").count()

    dados = {
        "total_labs": total_labs,
        "total_computadores": total_computadores,
        "pcs_funcionando": pcs_funcionando,
        "pcs_defeito": pcs_defeito,
        "pcs_manutencao": pcs_manutencao,
        "chamados_abertos": chamados_abertos,
        "chamados_em_andamento": chamados_em_andamento,
        "chamados_resolvidos": chamados_resolvidos,
    }

    if user.is_admin:
        dados["total_usuarios"] = Usuario.query.count()
        dados["reservas_futuras_total"] = reservas_futuras_query.count()
        dados["proximas_reservas"] = reservas_futuras_query.order_by(Reserva.data.asc(), Reserva.horario_inicio.asc()).limit(5).all()
        dados["ultimos_chamados"] = Chamado.query.order_by(Chamado.data_abertura.desc()).limit(5).all()

    elif user.is_professor:
        minhas_reservas_query = reservas_futuras_query.filter_by(professor_id=user.id)
        dados["minhas_reservas_count"] = minhas_reservas_query.count()
        dados["minhas_proximas_reservas"] = minhas_reservas_query.order_by(Reserva.data.asc(), Reserva.horario_inicio.asc()).limit(5).all()
        dados["meus_chamados_abertos"] = Chamado.query.filter_by(usuario_id=user.id, situacao="Aberto").count()
        dados["meus_ultimos_chamados"] = Chamado.query.filter_by(usuario_id=user.id).order_by(Chamado.data_abertura.desc()).limit(5).all()

    elif user.is_ti:
        dados["reservas_futuras_total"] = reservas_futuras_query.count()
        dados["chamados_pendentes"] = Chamado.query.filter(Chamado.situacao.in_(["Aberto", "Em andamento"])).order_by(Chamado.data_abertura.desc()).limit(5).all()
        dados["computadores_atencao"] = Computador.query.filter(Computador.estado.in_(["Com defeito", "Em manutenção"])).order_by(Computador.criado_em.desc()).limit(5).all()

    # Dados formatados para o Chart.js
    dados["chart_computadores"] = {
        "labels": ["Funcionando", "Com defeito", "Em manutenção"],
        "values": [pcs_funcionando, pcs_defeito, pcs_manutencao],
        "colors": ["#22C55E", "#F05261", "#F5B942"],
    }

    dados["chart_chamados"] = {
        "labels": ["Abertos", "Em andamento", "Resolvidos"],
        "values": [chamados_abertos, chamados_em_andamento, chamados_resolvidos],
        "colors": ["#F05261", "#F5B942", "#22C55E"],
    }

    return dados
