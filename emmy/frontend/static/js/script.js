/**
 * LABCONTROL 1.0 — Vanilla JS Client Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Gerenciamento de Alertas Flash
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const alert = btn.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 200);
            }
        });
    });

    // 2. Gerenciamento de Modais
    function openModal(modal) {
        if (!modal) return;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = trigger.getAttribute('data-modal-target');
            const modal = document.querySelector(targetId);
            openModal(modal);
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });

        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => closeModal(modal));
        }

        const cancelBtn = modal.querySelector('.btn-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => closeModal(modal));
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(closeModal);
        }
    });

    // 3. Carregamento Dinâmico de Computadores por Laboratório (Chamados)
    const selectLabChamado = document.getElementById('chamado-laboratorio-select');
    const selectPcChamado = document.getElementById('chamado-computador-select');

    if (selectLabChamado && selectPcChamado) {
        selectLabChamado.addEventListener('change', async () => {
            const labId = selectLabChamado.value;
            selectPcChamado.innerHTML = '<option value="">Nenhum (Problema geral no laboratório)</option>';
            if (!labId) return;

            try {
                const response = await fetch(`/laboratorios/api/${labId}/computadores`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.computadores && data.computadores.length > 0) {
                        data.computadores.forEach(pc => {
                            const opt = document.createElement('option');
                            opt.value = pc.id;
                            opt.textContent = `${pc.identificador} (${pc.hostname}) — [${pc.estado}]`;
                            selectPcChamado.appendChild(opt);
                        });
                    }
                }
            } catch (err) {
                console.error('Erro ao buscar computadores do laboratório:', err);
            }
        });
    }

    // 4. Verificação Dinâmica de Disponibilidade de Reservas
    const formReserva = document.getElementById('form-nova-reserva');
    const statusDisponibilidade = document.getElementById('reserva-status-feedback');

    if (formReserva && statusDisponibilidade) {
        const inputsToCheck = formReserva.querySelectorAll('select[name="laboratorio_id"], input[name="data"], input[name="horario_inicio"], input[name="horario_fim"], input[name="quantidade_alunos"]');

        const verificarDisponibilidade = async () => {
            const labId = formReserva.querySelector('select[name="laboratorio_id"]')?.value;
            const dataVal = formReserva.querySelector('input[name="data"]')?.value;
            const inicio = formReserva.querySelector('input[name="horario_inicio"]')?.value;
            const fim = formReserva.querySelector('input[name="horario_fim"]')?.value;
            const qtdAlunos = formReserva.querySelector('input[name="quantidade_alunos"]')?.value;

            if (!labId || !dataVal || !inicio || !fim || !qtdAlunos || parseInt(qtdAlunos) <= 0) {
                statusDisponibilidade.style.display = 'none';
                return;
            }

            statusDisponibilidade.style.display = 'block';
            statusDisponibilidade.className = 'alert alert-info';
            statusDisponibilidade.innerHTML = ' Verificando disponibilidade no banco de dados...';

            try {
                const csrfToken = formReserva.querySelector('input[name="csrf_token"]')?.value || '';
                const response = await fetch('/reservas/verificar-disponibilidade', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        laboratorio_id: labId,
                        data: dataVal,
                        horario_inicio: inicio,
                        horario_fim: fim,
                        quantidade_alunos: qtdAlunos
                    })
                });

                const resData = await response.json();
                if (resData.valido) {
                    statusDisponibilidade.className = 'alert alert-success';
                    statusDisponibilidade.innerHTML = ` ${resData.mensagem}`;
                } else {
                    statusDisponibilidade.className = 'alert alert-danger';
                    statusDisponibilidade.innerHTML = ` ${resData.mensagem}`;
                }
            } catch (err) {
                statusDisponibilidade.style.display = 'none';
            }
        };

        inputsToCheck.forEach(input => {
            input.addEventListener('change', verificarDisponibilidade);
            input.addEventListener('input', verificarDisponibilidade);
        });
    }

    // 5. Inicialização de Gráficos Chart.js do Dashboard
    if (window.dashboardChartsData && typeof Chart !== 'undefined') {
        const { chart_computadores, chart_chamados } = window.dashboardChartsData;

        // Gráfico de Equipamentos por Estado (Doughnut)
        const ctxPcs = document.getElementById('chartPcsStatus');
        if (ctxPcs) {
            new Chart(ctxPcs, {
                type: 'doughnut',
                data: {
                    labels: chart_computadores.labels,
                    datasets: [{
                        data: chart_computadores.values,
                        backgroundColor: chart_computadores.colors,
                        borderColor: '#302744',
                        borderWidth: 2,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#F5F2FA',
                                font: { family: 'Inter', size: 12 }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }

        // Gráfico de Chamados por Situação (Bar)
        const ctxChamados = document.getElementById('chartChamadosStatus');
        if (ctxChamados) {
            new Chart(ctxChamados, {
                type: 'bar',
                data: {
                    labels: chart_chamados.labels,
                    datasets: [{
                        label: 'Quantidade',
                        data: chart_chamados.values,
                        backgroundColor: chart_chamados.colors,
                        borderRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#B8ADC9', font: { family: 'Inter' } },
                            grid: { display: false }
                        },
                        y: {
                            ticks: {
                                color: '#B8ADC9',
                                font: { family: 'Inter' },
                                stepSize: 1,
                                precision: 0
                            },
                            grid: { color: 'rgba(64, 54, 83, 0.4)' }
                        }
                    }
                }
            });
        }
    }
});
