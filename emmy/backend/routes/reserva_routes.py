from datetime import datetime, date, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from backend.database import db
from backend.models.reserva import Reserva, SITUACOES_RESERVA
from backend.models.laboratorio import Laboratorio
from backend.services.auth_service import role_required
from backend.services.reserva_service import validar_reserva

reserva_bp = Blueprint("reservas", __name__)


@reserva_bp.route("/")
@login_required
def index():
    lab_id = request.args.get("laboratorio_id", "").strip()
    data_filtro = request.args.get("data", "").strip()
    situacao = request.args.get("situacao", "").strip()

    query = Reserva.query

    # Professores veem prioritariamente suas próprias reservas, a menos que selecionem histórico
    if current_user.is_professor:
        query = query.filter_by(professor_id=current_user.id)

    if lab_id and lab_id.isdigit():
        query = query.filter_by(laboratorio_id=int(lab_id))

    if data_filtro:
        try:
            data_obj = datetime.strptime(data_filtro, "%Y-%m-%d").date()
            query = query.filter_by(data=data_obj)
        except ValueError:
            pass

    if situacao in SITUACOES_RESERVA:
        query = query.filter_by(situacao=situacao)

    reservas = query.order_by(Reserva.data.desc(), Reserva.horario_inicio.desc()).all()
    laboratorios = Laboratorio.query.order_by(Laboratorio.identificador.asc()).all()

    return render_template(
        "reservas.html",
        reservas=reservas,
        laboratorios=laboratorios,
        situacoes=SITUACOES_RESERVA,
        lab_id=lab_id,
        data_filtro=data_filtro,
        situacao=situacao,
    )


@reserva_bp.route("/verificar-disponibilidade", methods=["POST"])
@login_required
def verificar_disponibilidade():
    """Valida disponibilidade em tempo real para feedback dinâmico no frontend."""
    dados = request.get_json(silent=True) or request.form
    try:
        lab_id = int(dados.get("laboratorio_id"))
        data_obj = datetime.strptime(dados.get("data"), "%Y-%m-%d").date()
        inicio_obj = datetime.strptime(dados.get("horario_inicio"), "%H:%M").time()
        fim_obj = datetime.strptime(dados.get("horario_fim"), "%H:%M").time()
        qtd_alunos = int(dados.get("quantidade_alunos"))
    except (ValueError, TypeError):
        return jsonify({"valido": False, "mensagem": "Dados incompletos ou formatos inválidos."}), 400

    valido, mensagem = validar_reserva(lab_id, data_obj, inicio_obj, fim_obj, qtd_alunos)
    return jsonify({"valido": valido, "mensagem": mensagem or "Horário e laboratório disponíveis para reserva!"})


@reserva_bp.route("/nova", methods=["POST"])
@login_required
@role_required("Professor", "Administrador")
def nova():
    lab_id_str = request.form.get("laboratorio_id", "").strip()
    turma = request.form.get("turma", "").strip()
    qtd_alunos_str = request.form.get("quantidade_alunos", "").strip()
    data_str = request.form.get("data", "").strip()
    inicio_str = request.form.get("horario_inicio", "").strip()
    fim_str = request.form.get("horario_fim", "").strip()
    finalidade = request.form.get("finalidade", "").strip()

    if not all([lab_id_str, turma, qtd_alunos_str, data_str, inicio_str, fim_str]):
        flash("Todos os campos obrigatórios devem ser preenchidos.", "danger")
        return redirect(url_for("reservas.index"))

    try:
        lab_id = int(lab_id_str)
        qtd_alunos = int(qtd_alunos_str)
        data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
        inicio_obj = datetime.strptime(inicio_str, "%H:%M").time()
        fim_obj = datetime.strptime(fim_str, "%H:%M").time()
    except ValueError:
        flash("Dados numéricos ou formatos de data/hora inválidos.", "danger")
        return redirect(url_for("reservas.index"))

    # Validação rigorosa de negócio
    valido, mensagem = validar_reserva(lab_id, data_obj, inicio_obj, fim_obj, qtd_alunos)
    if not valido:
        flash(mensagem, "danger")
        return redirect(url_for("reservas.index"))

    lab = db.session.get(Laboratorio, lab_id)
    reserva = Reserva(
        professor_id=current_user.id,
        laboratorio_id=lab.id,
        turma=turma,
        quantidade_alunos=qtd_alunos,
        data=data_obj,
        horario_inicio=inicio_obj,
        horario_fim=fim_obj,
        finalidade=finalidade or None,
        situacao="Confirmada",
    )
    db.session.add(reserva)
    db.session.commit()

    flash(
        f"Reserva do laboratório '{lab.identificador}' para a turma '{turma}' confirmada com sucesso!",
        "success"
    )
    return redirect(url_for("reservas.index"))


@reserva_bp.route("/<int:reserva_id>/cancelar", methods=["POST"])
@login_required
def cancelar(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)

    # Permissões: apenas o professor dono da reserva ou um Administrador pode cancelar
    if not current_user.is_admin and reserva.professor_id != current_user.id:
        flash("Você não tem permissão para cancelar uma reserva pertencente a outro professor.", "danger")
        return redirect(url_for("reservas.index"))

    if reserva.situacao == "Cancelada":
        flash("Esta reserva já se encontra cancelada.", "info")
        return redirect(url_for("reservas.index"))

    reserva.situacao = "Cancelada"
    db.session.commit()

    flash(f"Reserva #{reserva.id} cancelada com sucesso.", "success")
    return redirect(url_for("reservas.index"))
