from alembic import context
from app.db import engine, metadata

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
