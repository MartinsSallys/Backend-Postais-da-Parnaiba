import os
import sys

from app.core.security import get_password_hash
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.admin import Admin


def main() -> None:
    Base.metadata.create_all(bind=engine)

    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if not username or not password:
        if len(sys.argv) >= 3:
            username = sys.argv[1].strip()
            password = sys.argv[2].strip()

    if not username or not password:
        raise SystemExit(
            "Defina ADMIN_USERNAME e ADMIN_PASSWORD no .env "
            "ou passe como argumentos: python scripts/create_admin.py <user> <pass>"
        )

    with SessionLocal() as db:
        existing = db.query(Admin).filter(Admin.username == username).first()
        if existing is not None:
            print(f"Admin '{username}' ja existe.")
            return

        admin = Admin(username=username, hashed_password=get_password_hash(password))
        db.add(admin)
        db.commit()

    print(f"Admin '{username}' criado com sucesso.")


if __name__ == "__main__":
    main()
