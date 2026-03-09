from app.config import settings
from app.graph.builder import compile_graph

_graph = None
_saver_context = None


def _postgres_url(url: str) -> str:
    return url.replace("postgresql+psycopg", "postgresql", 1).replace(
        "postgresql+psycopg2", "postgresql", 1
    )


def open_checkpointer():
    """PostgresSaver is the production checkpointer. Tests use in-memory state."""
    if settings.database_url.startswith("sqlite"):
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver(), None
    from langgraph.checkpoint.postgres import PostgresSaver

    context = PostgresSaver.from_conn_string(_postgres_url(settings.database_url))
    saver = context.__enter__()
    saver.setup()
    return saver, context


def init_graph():
    global _graph, _saver_context
    if _graph is not None:
        return _graph
    saver, _saver_context = open_checkpointer()
    _graph = compile_graph(saver)
    return _graph


def get_graph():
    if _graph is None:
        return init_graph()
    return _graph


def shutdown_graph():
    global _graph, _saver_context
    if _saver_context is not None:
        _saver_context.__exit__(None, None, None)
    _graph = None
    _saver_context = None
