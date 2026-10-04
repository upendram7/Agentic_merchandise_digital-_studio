from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from sqlalchemy.engine import make_url

from app.core.config import settings


def _postgres_conninfo(database_url: str) -> str:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("DATABASE_URL must point to a PostgreSQL database")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


pool = ConnectionPool(
    conninfo=_postgres_conninfo(settings.database_url),
    min_size=0,
    max_size=5,
    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    open=False,
)
checkpointer = PostgresSaver(pool)


def init_checkpointer() -> None:
    if pool.closed:
        pool.open(wait=True)
    checkpointer.setup()
