from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from backend.database import db
from backend.models.computador import Computador, ESTADOS_COMPUTADOR
from backend.models.laboratorio import Laboratorio
from backend.models.chamado import Chamado
from backend.services.auth_service import role_required

pc_bp = Blueprint("computadores", __name__)


@pc_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    lab_id = request.args.get("laboratorio_id", "").strip()
    estado = request.args.get("estado", "").strip()

    query = Computador.query

    if q:
        query = query.filter(
            (Computador.identificador.ilike(f"%{q}%")) |
            (Computador.hostname.ilike(f"%{q}%"))
        )

    if lab_id and lab_id.isdigit():
        query = query.filter_by(laboratorio_id=int(lab_id))

    if estado and estado in ESTADOS_COMPUTADOR:
        query = query.filter_by(estado=estado)

    computadores = query.order_by(Computador.laboratorio_id.asc(), Computador.identificador.asc()).all()
    laboratorios = Laboratorio.query.order_by(Laboratorio.identificador.asc()).all()

    return render_template(
        "computadores.html",
        computadores=computadores,
        laboratorios=laboratorios,
        estados=ESTADOS_COMPUTADOR,
        q=q,
        lab_id=lab_id,
        estado=estado,
    )


@pc_bp.route("/novo", methods=["POST"])
@login_required
@role_required("Administrador", "TI")
def novo():
    identificador = request.form.get("identificador", "").strip().upper()
    hostname = request.form.get("hostname", "").strip().lower()
    lab_id_str = request.form.get("laboratorio_id", "").strip()
    estado = request.form.get("estado", "Funcionando").strip()
    observacao = request.form.get("observacao", "").strip()

    if not identificador or not hostname or not lab_id_str:
        flash("Identificador, hostname e laboratório são campos obrigatórios.", "danger")
        return redirect(url_for("computadores.index"))

    if estado not in ESTADOS_COMPUTADOR:
        flash("Estado de computador inválido.", "danger")
        return redirect(url_for("computadores.index"))

    try:
        lab_id = int(lab_id_str)
        lab = db.session.get(Laboratorio, lab_id)
        if not lab:
            raise ValueError()
    except ValueError:
        flash("Laboratório selecionado inválido.", "danger")
        return redirect(url_for("computadores.index"))

    if Computador.query.filter_by(identificador=identificador).first():
        flash(f"Já existe um computador cadastrado com o identificador '{identificador}'.", "danger")
        return redirect(url_for("computadores.index"))

    pc = Computador(
        identificador=identificador,
        hostname=hostname,
        laboratorio_id=lab.id,
        estado=estado,
        observacao=observacao or None,
    )
    db.session.add(pc)
    db.session.commit()

    flash(f"Computador '{pc.identificador}' ({pc.hostname}) cadastrado com sucesso no {lab.identificador}!", "success")
    return redirect(url_for("computadores.index"))


@pc_bp.route("/<int:pc_id>/editar", methods=["POST"])
@login_required
@role_required("Administrador", "TI")
def editar(pc_id):
    pc = Computador.query.get_or_404(pc_id)

    identificador = request.form.get("identificador", "").strip().upper()
    hostname = request.form.get("hostname", "").strip().lower()
    lab_id_str = request.form.get("laboratorio_id", "").strip()
    estado = request.form.get("estado", "").strip()
    observacao = request.form.get("observacao", "").strip()

    if not identificador or not hostname or not lab_id_str:
        flash("Identificador, hostname e laboratório são obrigatórios.", "danger")
        return redirect(url_for("computadores.index"))

    if estado not in ESTADOS_COMPUTADOR:
        flash("Estado informado é inválido.", "danger")
        return redirect(url_for("computadores.index"))

    try:
        lab_id = int(lab_id_str)
        lab = db.session.get(Laboratorio, lab_id)
        if not lab:
            raise ValueError()
    except ValueError:
        flash("Laboratório selecionado inválido.", "danger")
        return redirect(url_for("computadores.index"))

    # Checar identificador duplicado
    existente = Computador.query.filter(Computador.identificador == identificador, Computador.id != pc_id).first()
    if existente:
        flash(f"O identificador '{identificador}' já está em uso por outro equipamento.", "danger")
        return redirect(url_for("computadores.index"))

    pc.identificador = identificador
    pc.hostname = hostname
    pc.laboratorio_id = lab.id
    pc.estado = estado
    pc.observacao = observacao or None

    db.session.commit()
    flash(f"Dados do computador '{pc.identificador}' atualizados com sucesso!", "success")
    return redirect(url_for("computadores.index"))


@pc_bp.route("/<int:pc_id>/atualizar-estado", methods=["POST"])
@login_required
@role_required("Administrador", "TI")
def atualizar_estado(pc_id):
    """Atualização rápida do estado de um computador."""
    pc = Computador.query.get_or_404(pc_id)
    novo_estado = request.form.get("estado", "").strip()
    obs_adicional = request.form.get("observacao", "").strip()

    if novo_estado not in ESTADOS_COMPUTADOR:
        flash("Estado selecionado inválido.", "danger")
        return redirect(url_for("computadores.index"))

    pc.estado = novo_estado
    if obs_adicional:
        pc.observacao = obs_adicional

    db.session.commit()
    flash(f"Estado do computador '{pc.identificador}' alterado para '{pc.estado}'!", "success")
    return redirect(url_for("computadores.index"))


@pc_bp.route("/<int:pc_id>/excluir", methods=["POST"])
@login_required
@role_required("Administrador", "TI")
def excluir(pc_id):
    pc = Computador.query.get_or_404(pc_id)

    # Verificar chamados abertos ou em andamento vinculados ao computador
    chamados_ativos = pc.chamados.filter(Chamado.situacao.in_(["Aberto", "Em andamento"])).count()
    if chamados_ativos > 0:
        flash(
            f"Não é possível excluir o computador '{pc.identificador}' pois há {chamados_ativos} chamados técnicos em andamento vinculados a ele.",
            "danger"
        )
        return redirect(url_for("computadores.index"))

    identificador = pc.identificador
    db.session.delete(pc)
    db.session.commit()
    flash(f"Computador '{identificador}' excluído com sucesso.", "success")
    return redirect(url_for("computadores.index"))
