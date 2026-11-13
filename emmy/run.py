import os
import sys
from backend.app import create_app
from backend.database import db

app = create_app()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        from backend.cli import init_db
        init_db()
    elif len(sys.argv) > 1 and sys.argv[1] == "seed":
        from backend.cli import seed_demo_data
        seed_demo_data()
    elif len(sys.argv) > 1 and sys.argv[1] == "create-admin":
        from backend.cli import create_admin_interactive
        create_admin_interactive()
    else:
        # Garante que as tabelas existam ao iniciar
        with app.app_context():
            db.create_all()
        port = int(os.environ.get("PORT", 5000))
        debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
        print(f"🚀 LabControl 1.0 rodando em http://127.0.0.1:{port}")
        app.run(host="0.0.0.0", port=port, debug=debug)
