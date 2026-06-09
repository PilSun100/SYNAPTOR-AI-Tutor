import json
from collections.abc import Iterable

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import Text, TypeDecorator, UserDefinedType


class PGVector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dimensions})"


@compiles(PGVector, "postgresql")
def _compile_pgvector_postgresql(type_: PGVector, *_: object, **__: object) -> str:
    return f"vector({type_.dimensions})"


@compiles(PGVector, "sqlite")
def _compile_pgvector_sqlite(_: PGVector, *__: object, **___: object) -> str:
    return "TEXT"


@compiles(PGVector)
def _compile_pgvector_default(_: PGVector, *__: object, **___: object) -> str:
    return "TEXT"


class EmbeddingVector(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGVector(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Iterable[float] | None, dialect):
        if value is None:
            return None

        embedding = [float(item) for item in value]
        if dialect.name == "postgresql":
            return "[" + ",".join(f"{item:.8f}" for item in embedding) + "]"
        return json.dumps(embedding, separators=(",", ":"))

    def process_result_value(self, value: object, _: object) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return [float(item) for item in value]
        if isinstance(value, tuple):
            return [float(item) for item in value]
        if not isinstance(value, str):
            return None

        raw = value.strip()
        if not raw:
            return None

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [float(item) for item in parsed]
        except json.JSONDecodeError:
            pass

        return [float(item) for item in raw.strip("[]").split(",") if item.strip()]
