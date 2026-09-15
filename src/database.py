from pathlib import Path

from src.db.connection import DatabaseConfigurationError, database_connection, get_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / "migrations"


def run_migrations() -> list[str]:
    try:
        with database_connection() as connection:
            migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
            if not migration_files:
                return []

            applied_migrations: list[str] = []
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        name VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )

                for migration_file in migration_files:
                    migration_name = migration_file.name
                    cursor.execute("SELECT 1 FROM schema_migrations WHERE name = %s", (migration_name,))
                    if cursor.fetchone() is not None:
                        continue

                    sql = migration_file.read_text(encoding="utf-8")
                    cursor.execute(sql)
                    cursor.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (migration_name,))
                    applied_migrations.append(migration_name)

            connection.commit()
            return applied_migrations
    except Exception:
        return []


def initialize_database() -> bool:
    return bool(run_migrations())


if __name__ == "__main__":
    applied = run_migrations()
    if applied:
        print(f"Applied migrations: {', '.join(applied)}")
    else:
        print("No migrations to apply.")
