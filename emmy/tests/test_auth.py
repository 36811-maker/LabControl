from backend.models.usuario import Usuario
from backend.database import db


def test_password_hashing(app):
    with app.app_context():
        u = Usuario(nome="Teste", email="t@t.com", username="teste", perfil="Professor")
        u.set_senha("senhaSecreta123")
        assert u.senha_hash != "senhaSecreta123"
        assert u.check_senha("senhaSecreta123") is True
        assert u.check_senha("senhaErrada") is False


def test_login_success_username(client, seed_test_data):
    response = client.post("/login", data={
        "identificador": "prof.roberto",
        "senha": "prof123",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Bem-vindo" in response.data


def test_login_success_email(client, seed_test_data):
    response = client.post("/login", data={
        "identificador": "roberto@teste.com",
        "senha": "prof123",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Bem-vindo" in response.data


def test_login_failed_password(client, seed_test_data):
    response = client.post("/login", data={
        "identificador": "prof.roberto",
        "senha": "senhaInvalida",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Usuário ou senha incorretos".encode("utf-8") in response.data


def test_inactive_user_cannot_login(client, seed_test_data):
    response = client.post("/login", data={
        "identificador": "inativo",
        "senha": "inativo123",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Esta conta está desativada".encode("utf-8") in response.data


def test_professor_cannot_access_usuarios_page(client, seed_test_data):
    # Login como professor
    client.post("/login", data={"identificador": "prof.roberto", "senha": "prof123"})
    # Tenta acessar gerenciamento de usuários
    response = client.get("/usuarios/", follow_redirects=True)
    assert response.status_code == 200
    assert "Acesso não autorizado para o seu perfil".encode("utf-8") in response.data


def test_admin_can_access_usuarios_page(client, seed_test_data):
    # Login como administrador
    client.post("/login", data={"identificador": "admin", "senha": "admin123"})
    response = client.get("/usuarios/")
    assert response.status_code == 200
    assert "Gerenciamento de Usuários".encode("utf-8") in response.data
