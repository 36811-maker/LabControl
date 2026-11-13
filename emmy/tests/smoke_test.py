import re
from backend.app import create_app

app = create_app()
client = app.test_client()

def login_user(username, password):
    r_get = client.get('/login')
    match = re.search(r'name="csrf_token" value="([^"]+)"', r_get.data.decode("utf-8"))
    token = match.group(1) if match else ""
    return client.post('/login', data={
        'identificador': username,
        'senha': password,
        'csrf_token': token
    }, follow_redirects=True)

# 1. Testar Administrador
print("--- Testando Administrador ---")
res = login_user("admin", "AdminSecure@2026")
assert res.status_code == 200
assert "Painel Geral" in res.data.decode("utf-8")
print("Login Admin OK")

for route in ['/', '/laboratorios/', '/computadores/', '/reservas/', '/chamados/', '/usuarios/']:
    r = client.get(route)
    assert r.status_code == 200
    print(f"GET {route} -> 200 OK")

client.get('/logout')

# 2. Testar Professor
print("\n--- Testando Professor ---")
res_prof = login_user("prof.carlos", "ProfSecure@2026")
assert res_prof.status_code == 200
assert "Painel Geral" in res_prof.data.decode("utf-8")
print("Login Professor OK")

for route in ['/', '/laboratorios/', '/computadores/', '/reservas/', '/chamados/']:
    r = client.get(route)
    assert r.status_code == 200
    print(f"GET {route} -> 200 OK")

# Professor não pode acessar /usuarios
r_block = client.get('/usuarios/', follow_redirects=True)
assert r_block.status_code == 200
assert "Acesso não autorizado para o seu perfil" in r_block.data.decode("utf-8")
print("Bloqueio de perfil não-autorizado OK")

client.get('/logout')

# 3. Testar TI
print("\n--- Testando TI ---")
res_ti = login_user("ti.lucas", "TISecure@2026")
assert res_ti.status_code == 200
assert "Painel Geral" in res_ti.data.decode("utf-8")
print("Login TI OK")

for route in ['/', '/laboratorios/', '/computadores/', '/reservas/', '/chamados/']:
    r = client.get(route)
    assert r.status_code == 200
    print(f"GET {route} -> 200 OK")

print("\n TODOS OS TESTES DE SMOKE E ROTAS PASSARAM COM SUCESSO!")
