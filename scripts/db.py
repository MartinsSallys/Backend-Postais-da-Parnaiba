import shutil
import subprocess
import sys
import time

CONTAINER_NAME = "postais-da-parnaiba-postgres"
VOLUME_NAME = "backend-postais_da_parnaiba_postgres_data"
IMAGE = "docker.io/library/postgres:16"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "postais_da_parnaiba"
DB_PORT = "5432"


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True)


def command_works(command: list[str]) -> bool:
    try:
        subprocess.run(
            command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


def compose_command() -> list[str] | None:
    if shutil.which("docker") and command_works(["docker", "compose", "version"]):
        return ["docker", "compose"]
    if shutil.which("docker-compose") and command_works(["docker-compose", "version"]):
        return ["docker-compose"]
    if shutil.which("podman") and command_works(["podman", "compose", "version"]):
        return ["podman", "compose"]
    return None


def podman_up() -> None:
    if not shutil.which("podman"):
        raise SystemExit("Docker Compose nao encontrado e Podman nao esta disponivel.")

    run(["podman", "volume", "create", VOLUME_NAME], check=False)

    exists = (
        subprocess.run(
            ["podman", "container", "exists", CONTAINER_NAME],
            check=False,
        ).returncode
        == 0
    )

    if exists:
        run(["podman", "start", CONTAINER_NAME], check=False)
    else:
        run(
            [
                "podman",
                "run",
                "-d",
                "--name",
                CONTAINER_NAME,
                "-e",
                f"POSTGRES_USER={DB_USER}",
                "-e",
                f"POSTGRES_PASSWORD={DB_PASSWORD}",
                "-e",
                f"POSTGRES_DB={DB_NAME}",
                "-p",
                f"{DB_PORT}:5432",
                "-v",
                f"{VOLUME_NAME}:/var/lib/postgresql/data",
                IMAGE,
            ]
        )


def podman_down() -> None:
    if not shutil.which("podman"):
        raise SystemExit("Docker Compose nao encontrado e Podman nao esta disponivel.")
    run(["podman", "stop", CONTAINER_NAME], check=False)
    run(["podman", "rm", CONTAINER_NAME], check=False)


def wait_until_ready() -> None:
    for _ in range(30):
        result = subprocess.run(
            [
                "podman",
                "exec",
                CONTAINER_NAME,
                "pg_isready",
                "-U",
                DB_USER,
                "-d",
                DB_NAME,
            ],
            check=False,
            text=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise SystemExit("PostgreSQL nao ficou pronto dentro do tempo esperado.")


def up() -> None:
    compose = compose_command()
    if compose is not None:
        run([*compose, "up", "-d", "postgres"])
        return
    podman_up()
    wait_until_ready()


def down() -> None:
    compose = compose_command()
    if compose is not None:
        run([*compose, "down"])
        return
    podman_down()


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"up", "down"}:
        raise SystemExit("Uso: python scripts/db.py [up|down]")

    if sys.argv[1] == "up":
        up()
    else:
        down()


if __name__ == "__main__":
    main()
