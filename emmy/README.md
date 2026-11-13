# LabControl 1.0 — Sistema de Gerenciamento de Laboratórios de Informática

O **LabControl** é um sistema web desenvolvido para centralizar e otimizar o gerenciamento de laboratórios de informática escolares, integrando professores, técnicos de TI e administradores em um único ambiente moderno, ágil e seguro.

---

## 🎨 Identidade Visual — Midnight Purple

Desenvolvido com o tema escuro corporativo **Midnight Purple**, apresentando alto contraste, elegância e foco na usabilidade:

| Elemento | Hexadecimal |
|---|---|
| Fundo principal | `#171323` |
| Fundo secundário | `#211A38` |
| Superfícies e cards | `#302744` |
| Roxo profundo | `#49376B` |
| Roxo elétrico | `#7656B9` |
| Roxo vibrante | `#9275D8` |
| Lavanda | `#C6B5F0` |
| Texto principal | `#F5F2FA` |
| Texto secundário | `#B8ADC9` |
| Destaques | Ciano (`#45D6E8`), Rosa (`#E58ACB`), Azul (`#668CFF`) |
| Estados | Funcionando (`#22C55E`), Defeito (`#F05261`), Manutenção (`#F5B942`) |

---

## 🚀 Tecnologias Utilizadas

- **Frontend:** HTML5 semântico, CSS3 com variáveis nativas e transições suaves (180ms–250ms), Vanilla JS (sem frameworks externos pesados) e **Chart.js** para renderização dos gráficos do dashboard.
- **Backend:** Python 3.14 + **Flask**, **Flask-SQLAlchemy** e **Flask-Login**.
- **Banco de Dados:** **SQLite** para execução local (`instance/labcontrol.db`), com arquitetura desacoplada e compatível para futura migração para **PostgreSQL**.
- **Segurança:** Senhas protegidas com hash criptográfico (Werkzeug pbkdf2/scrypt), proteção integrada contra CSRF, controle de sessão segura e verificação estrita de perfis tanto no frontend quanto no backend.

---

## 👥 Perfis de Acesso e Permissões

1. **Administrador**
   - Gestão completa de usuários (criação, edição, bloqueio/desativação).
   - Cadastro, edição e exclusão de laboratórios (com validações de integridade referencial).
   - Gerenciamento e acompanhamento global de computadores, reservas e chamados.

2. **Professor**
   - Consulta de laboratórios e computadores funcionando em tempo real.
   - Realização de reservas com verificação rigorosa de capacidade e conflitos de horários.
   - Consulta e cancelamento de suas próprias reservas.
   - Abertura de chamados técnicos e acompanhamento do status.

3. **Técnico de TI**
   - Cadastro, edição e acompanhamento de inventário de equipamentos.
   - Atualização manual do estado operacional dos computadores (*Funcionando*, *Com defeito*, *Em manutenção*).
   - Triagem, atendimento, atribuição de responsável e resolução de chamados técnicos com registro de data de conclusão.

---

## 📦 Estrutura do Projeto

```
LabControl/
│
├── backend/
│   ├── app.py                     # Application Factory do Flask & tratamento de erros
│   ├── config.py                  # Configurações de ambiente, sessão e banco
│   ├── database.py                # Instância central do SQLAlchemy
│   ├── cli.py                     # Comandos de terminal (init-db, create-admin, seed)
│   ├── models/                    # Modelos de dados relacionais
│   │   ├── usuario.py
│   │   ├── laboratorio.py
│   │   ├── computador.py
│   │   ├── reserva.py
│   │   └── chamado.py
│   ├── routes/                    # Blueprints e rotas HTTP do sistema
│   │   ├── auth_routes.py
│   │   ├── dashboard_routes.py
│   │   ├── laboratorio_routes.py
│   │   ├── computador_routes.py
│   │   ├── reserva_routes.py
│   │   ├── chamado_routes.py
│   │   └── usuario_routes.py
│   └── services/                  # Regras de negócio e validações
│       ├── auth_service.py        # RBAC, CSRF e validação de senhas
│       ├── dashboard_service.py   # Métricas em tempo real e dados de gráficos
│       └── reserva_service.py     # Validação de capacidade, computadores e horários
│
├── frontend/
│   ├── templates/                 # Templates Jinja2
│   │   ├── base.html              # Layout mestre com Sidebar Midnight Purple
│   │   ├── login.html             # Tela de login e autenticação
│   │   ├── setup.html             # Assistente de primeiro administrador
│   │   ├── dashboard.html         # Dashboard com Chart.js e visão por perfil
│   │   ├── laboratorios.html      # Catálogo e CRUD de laboratórios
│   │   ├── laboratorio_detalhe.html
│   │   ├── computadores.html      # Inventário com filtros e atualização de status
│   │   ├── reservas.html          # Agendamentos com verificação em tempo real
│   │   ├── chamados.html          # Fila técnica e acompanhamento
│   │   ├── usuarios.html          # Gerenciamento de acessos (Admin)
│   │   └── errors/                # Páginas de erro 403, 404 e 500
│   └── static/
│       ├── css/
│       │   └── style.css          # Folha de estilo completa Midnight Purple
│       └── js/
│           ├── script.js          # Modais, filtros dinâmicos e validação assíncrona
│           └── chart.min.js       # Chart.js local (suporte 100% offline)
│
├── instance/
│   └── labcontrol.db              # Banco de dados local SQLite
│
├── tests/                         # Suíte de testes automatizados com Pytest
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_laboratorios.py
│   ├── test_computadores.py
│   ├── test_reservas.py
│   └── test_chamados.py
│
├── requirements.txt
├── run.py                         # Ponto de entrada da aplicação
└── README.md
```

---

## 🛠️ Como Executar o Projeto

### 1. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 2. Inicializar o Banco de Dados

Você pode escolher entre duas formas de inicialização:

#### Opção A — Popular com Dados de Demonstração (Recomendado para Testes)

```bash
python run.py seed
```

Esta opção cria laboratórios, dezenas de computadores inventariados, chamados em aberto e três contas prontas para uso imediato:

- **Administrador:** `admin` / senha: `AdminSecure@2026`
- **Professor:** `prof.carlos` / senha: `ProfSecure@2026`
- **Técnico de TI:** `ti.lucas` / senha: `TISecure@2026`

#### Opção B — Inicialização Segura do Primeiro Administrador (Sem Senhas Fixas)

```bash
python run.py create-admin
```

Será solicitado no terminal o nome, e-mail, username e uma senha segura com confirmação mascarada.

### 3. Iniciar o Servidor Web

```bash
python run.py
```

Acesse em seu navegador: **`http://127.0.0.1:5000`**

---

## 🧪 Executando os Testes Automatizados

O projeto conta com suíte de testes cobrindo todas as 6 funcionalidades obrigatórias, regras de negócio de reservas, bloqueio de deleções com dependências e controle de acessos:

```bash
python -m pytest tests -v
```
