from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from backend.database import db
from backend.models.chamado import Chamado, SITUACOES_CHAMADO
from backend.models.laboratorio import Laboratorio
from backend.models.computador import Computador
from backend.models.usuario import Usuario
from backend.services.auth_service import role_required

chamado_bp = Blueprint("chamados", __name__)


def gerar_numero_chamado():
    ano = datetime.now().year
    ultimo = Chamado.query.filter(Chamado.numero_chamado.like(f"CHM-{ano}-%")).order_by(Chamado.id.desc()).first()
    if ultimo:
        try:
            num = int(ultimo.numero_chamado.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"CHM-{ano}-{num:04d}"


@chamado_bp.route("/")
@login_required
def index():
    situacao = request.args.get("situacao", "").strip()
    lab_id = request.args.get("laboratorio_id", "").strip()

    query = Chamado.query

    # Professor vê prioritariamente seus próprios chamados
    if current_user.is_professor:
        query = query.filter_by(usuario_id=current_user.id)

    if situacao in SITUACOES_CHAMADO:
        query = query.filter_by(situacao=situacao)

    if lab_id and lab_id.isdigit():
        query = query.filter_by(laboratorio_id=int(lab_id))

    chamados = query.order_by(Chamado.data_abertura.desc()).all()
    laboratorios = Laboratorio.query.order_by(Laboratorio.identificador.asc()).all()
    tecnicos = Usuario.query.filter(Usuario.perfil.in_(["TI", "Administrador"]), Usuario.ativo == True).all()

    return render_template(
        "chamados.html",
        chamados=chamados,
        laboratorios=laboratorios,
        situacoes=SITUACOES_CHAMADO,
        tecnicos=tecnicos,
        situacao=situacao,
        lab_id=lab_id,
    )


@chamado_bp.route("/novo", methods=["POST"])
@login_required
def novo():
    lab_id_str = request.form.get("laboratorio_id", "").strip()
    pc_id_str = request.form.get("computador_id", "").strip()
    descricao = request.form.get("descricao", "").strip()
    marcar_defeito = request.form.get("marcar_defeito") == "1"

    if not lab_id_str or not descricao:
        flash("Laboratório e descrição do problema são obrigatórios.", "danger")
        return redirect(url_for("chamados.index"))

    try:
        lab_id = int(lab_id_str)
        lab = db.session.get(Laboratorio, lab_id)
        if not lab:
            raise ValueError()
    except ValueError:
        flash("Laboratório selecionado inválido.", "danger")
        return redirect(url_for("chamados.index"))

    pc = None
    if pc_id_str and pc_id_str.isdigit():
        pc = Computador.query.filter_by(id=int(pc_id_str), laboratorio_id=lab.id).first()

    numero = gerar_numero_chamado()
    chamado = Chamado(
        numero_chamado=numero,
        usuario_id=current_user.id,
        laboratorio_id=lab.id,
        computador_id=pc.id if pc else None,
        descricao=descricao,
        situacao="Aberto",
    )
    db.session.add(chamado)

    # Se selecionou um computador e optou por marcar como defeito
    if pc and marcar_defeito and pc.estado == "Funcionando":
        pc.estado = "Com defeito"
        pc.observacao = f"Chamado {numero}: {descricao}"

    db.session.commit()
    flash(f"Chamado {numero} aberto com sucesso! Nossa equipe técnica foi notificada.", "success")
    return redirect(url_for("chamados.index"))


@chamado_bp.route("/<int:chamado_id>/atualizar", methods=["POST"])
@login_required
@role_required("Administrador", "TI")
def atualizar(chamado_id):
    chamado = Chamado.query.get_or_404(chamado_id)

    nova_situacao = request.form.get("situacao", "").strip()
    responsavel_id_str = request.form.get("responsavel_id", "").strip()
    nota_atendimento = request.form.get("nota_atendimento", "").strip()
    atualizar_pc_estado = request.form.get("pc_estado", "").strip()

    if nova_situacao not in SITUACOES_CHAMADO:
        flash("Situação informada inválida.", "danger")
        return redirect(url_for("chamados.index"))

    chamado.situacao = nova_situacao

    if responsavel_id_str and responsavel_id_str.isdigit():
        resp = db.session.get(Usuario, int(responsavel_id_str))
        if resp and resp.perfil in ["TI", "Administrador"]:
            chamado.responsavel_id = resp.id
    elif not chamado.responsavel_id:
        # Se não há responsável definido, atribui o técnico atual
        chamado.responsavel_id = current_user.id

    if nota_atendimento:
        chamado.nota_atendimento = nota_atendimento

    if nova_situacao == "Resolvido":
        chamado.data_conclusao = datetime.now(timezone.utc)
        # Se for especificado para colocar o computador de volta em Funcionando
        if chamado.computador and atualizar_pc_estado in ["Funcionando", "Com defeito", "Em manutenção"]:
            chamado.computador.estado = atualizar_pc_estado
    else:
        chamado.data_conclusao = None
        if chamado.computador and atualizar_pc_estado in ["Funcionando", "Com defeito", "Em manutenção"]:
            chamado.computador.estado = atualizar_pc_estado

    db.session.commit()
    flash(f"Chamado {chamado.numero_chamado} atualizado para '{chamado.situacao}' com sucesso!", "success")
    return redirect(url_for("chamados.index"))
