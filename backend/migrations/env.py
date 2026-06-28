import os

from alembic import context
from sqlalchemy import URL, engine_from_config, pool


config = context.config
target_metadata = None


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def database_url():
    return URL.create(
        "mysql+pymysql",
        username=os.environ.get("DB_MIGRATION_USER") or required_env("DB_USER"),
        password=os.environ.get("DB_MIGRATION_PASSWORD") or required_env("DB_PASSWORD"),
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        database=required_env("DB_NAME"),
        query={"charset": "utf8mb4"},
    )


def run_migrations_offline():
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url().render_as_string(
        hide_password=False
    )
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
