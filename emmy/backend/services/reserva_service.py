from datetime import date, time, datetime
from backend.database import db
from backend.models.laboratorio import Laboratorio
from backend.models.reserva import Reserva


def validar_reserva(laboratorio_id: int, data_reserva: date, inicio: time, fim: time, qtd_alunos: int, reserva_id_ignorar: int = None) -> tuple[bool, str]:
    """
    Executa todas as validações obrigatórias de negócio para criação ou alteração de reserva.
    Retorna (valido: bool, mensagem_erro: str).
    """
    # 1. Verificar se o laboratório existe
    lab = db.session.get(Laboratorio, laboratorio_id)
    if not lab:
        return False, "Laboratório informado não foi encontrado."

    # 6. Impedir reservas com quantidade de alunos igual ou inferior a zero
    if qtd_alunos <= 0:
        return False, "A quantidade de alunos deve ser maior que zero."

    # 5 e 7. Impedir reservas com horários ou datas inválidos
    hoje = date.today()
    if data_reserva < hoje:
        return False, "Não é permitido realizar reservas para datas no passado."

    if inicio >= fim:
        return False, "O horário de início deve ser estritamente anterior ao horário de término."

    agora = datetime.now()
    if data_reserva == hoje and inicio <= agora.time():
        return False, "O horário de início selecionado já passou para o dia de hoje."

    # 2. Verificar se a capacidade física máxima comporta os alunos
    if qtd_alunos > lab.capacidade_maxima:
        return False, f"A capacidade máxima do laboratório ({lab.capacidade_maxima} alunos) é inferior à turma informada ({qtd_alunos} alunos)."

    # 3. Verificar a quantidade de computadores funcionando
    pcs_funcionando = lab.computadores_funcionando
    if qtd_alunos > pcs_funcionando:
        return False, f"O laboratório '{lab.identificador}' possui apenas {pcs_funcionando} computadores funcionando, insuficiente para a quantidade de {qtd_alunos} alunos solicitada."

    # 4. Verificar se já existe outra reserva no mesmo laboratório em horário conflitante
    query_conflito = Reserva.query.filter(
        Reserva.laboratorio_id == lab.id,
        Reserva.data == data_reserva,
        Reserva.situacao == "Confirmada",
        Reserva.horario_inicio < fim,
        Reserva.horario_fim > inicio,
    )

    if reserva_id_ignorar:
        query_conflito = query_conflito.filter(Reserva.id != reserva_id_ignorar)

    conflito = query_conflito.first()
    if conflito:
        return False, (
            f"Conflito de horário: O laboratório já está reservado das "
            f"{conflito.horario_inicio.strftime('%H:%M')} às {conflito.horario_fim.strftime('%H:%M')} "
            f"pelo(a) {conflito.professor.nome} (Turma: {conflito.turma})."
        )

    return True, ""
