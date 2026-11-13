from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from backend.database import db
from backend.models.laboratorio import Laboratorio
from backend.models.computador import Computador
from backend.models.reserva import Reserva
from backend.models.chamado import Chamado
from backend.services.auth_service import role_required

lab_bp = Blueprint("laboratorios", __name__)


@lab_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()

    query = Laboratorio.query
    if q:
        query = query.filter(
            (Laboratorio.nome.ilike(f"%{q}%")) |
            (Laboratorio.identificador.ilike(f"%{q}%"))
        )

    laboratorios = query.order_by(Laboratorio.identificador.asc()).all()
    return render_template("laboratorios.html", laboratorios=laboratorios, q=q)


@lab_bp.route("/<int:lab_id>")
@login_required
def detalhes(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    computadores = laboratorio.computadores.order_by(Computador.identificador.asc()).all()
    return render_template("laboratorio_detalhe.html", laboratorio=laboratorio, computadores=computadores)


@lab_bp.route("/api/<int:lab_id>/computadores")
@login_required
def api_computadores(lab_id):
    """Endpoint JSON para carregar os computadores de um laboratório em formulários dinâmicos de chamados."""
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    pcs = [
        {"id": pc.id, "identificador": pc.identificador, "hostname": pc.hostname, "estado": pc.estado}
        for pc in laboratorio.computadores.order_by(Computador.identificador.asc()).all()
    ]
    return jsonify({
        "capacidade_maxima": laboratorio.capacidade_maxima,
        "computadores_funcionando": laboratorio.computadores_funcionando,
        "computadores": pcs,
    })


@lab_bp.route("/novo", methods=["POST"])
@login_required
@role_required("Administrador")
def novo():
    identificador = request.form.get("identificador", "").strip().upper()
    nome = request.form.get("nome", "").strip()
    capacidade_str = request.form.get("capacidade_maxima", "").strip()
    descricao = request.form.get("descricao", "").strip()

    if not identificador or not nome or not capacidade_str:
        flash("Identificador, nome e capacidade máxima são obrigatórios.", "danger")
        return redirect(url_for("laboratorios.index"))

    try:
        capacidade = int(capacidade_str)
        if capacidade <= 0:
            raise ValueError()
    except ValueError:
        flash("A capacidade máxima deve ser um número inteiro positivo maior que zero.", "danger")
        return redirect(url_for("laboratorios.index"))

    if Laboratorio.query.filter_by(identificador=identificador).first():
        flash(f"Já existe um laboratório com o identificador '{identificador}'.", "danger")
        return redirect(url_for("laboratorios.index"))

    lab = Laboratorio(
        identificador=identificador,
        nome=nome,
        capacidade_maxima=capacidade,
        descricao=descricao or None,
    )
    db.session.add(lab)
    db.session.commit()

    flash(f"Laboratório '{lab.nome}' ({lab.identificador}) cadastrado com sucesso!", "success")
    return redirect(url_for("laboratorios.index"))


@lab_bp.route("/<int:lab_id>/editar", methods=["POST"])
@login_required
@role_required("Administrador")
def editar(lab_id):
    lab = Laboratorio.query.get_or_404(lab_id)

    identificador = request.form.get("identificador", "").strip().upper()
    nome = request.form.get("nome", "").strip()
    capacidade_str = request.form.get("capacidade_maxima", "").strip()
    descricao = request.form.get("descricao", "").strip()

    if not identificador or not nome or not capacidade_str:
        flash("Identificador, nome e capacidade máxima são obrigatórios.", "danger")
        return redirect(url_for("laboratorios.index"))

    try:
        capacidade = int(capacidade_str)
        if capacidade <= 0:
            raise ValueError()
    except ValueError:
        flash("A capacidade máxima deve ser um número inteiro maior que zero.", "danger")
        return redirect(url_for("laboratorios.index"))

    existente = Laboratorio.query.filter(Laboratorio.identificador == identificador, Laboratorio.id != lab_id).first()
    if existente:
        flash(f"O identificador '{identificador}' já está em uso por outro laboratório.", "danger")
        return redirect(url_for("laboratorios.index"))

    lab.identificador = identificador
    lab.nome = nome
    lab.capacidade_maxima = capacidade
    lab.descricao = descricao or None

    db.session.commit()
    flash(f"Laboratório '{lab.nome}' atualizado com sucesso!", "success")
    return redirect(url_for("laboratorios.index"))


@lab_bp.route("/<int:lab_id>/excluir", methods=["POST"])
@login_required
@role_required("Administrador")
def excluir(lab_id):
    lab = Laboratorio.query.get_or_404(lab_id)

    # 1. Verificar se possui reservas ativas ou históricas
    total_reservas = Reserva.query.filter_by(laboratorio_id=lab.id).count()
    if total_reservas > 0:
        flash(
            f"Não é possível excluir o laboratório '{lab.identificador}' porque existem {total_reservas} reservas registradas nele.",
            "danger"
        )
        return redirect(url_for("laboratorios.index"))

    # 2. Verificar se possui computadores vinculados
    total_pcs = Computador.query.filter_by(laboratorio_id=lab.id).count()
    if total_pcs > 0:
        flash(
            f"Não é possível excluir o laboratório '{lab.identificador}' pois há {total_pcs} computadores cadastrados nele. Remova os equipamentos primeiro.",
            "danger"
        )
        return redirect(url_for("laboratorios.index"))

    # 3. Verificar chamados
    total_chamados = Chamado.query.filter_by(laboratorio_id=lab.id).count()
    if total_chamados > 0:
        flash(
            f"Não é possível excluir o laboratório '{lab.identificador}' pois há {total_chamados} chamados técnicos vinculados.",
            "danger"
        )
        return redirect(url_for("laboratorios.index"))

    db.session.delete(lab)
    db.session.commit()
    flash(f"Laboratório '{lab.identificador}' excluído com sucesso.", "success")
    return redirect(url_for("laboratorios.index"))
