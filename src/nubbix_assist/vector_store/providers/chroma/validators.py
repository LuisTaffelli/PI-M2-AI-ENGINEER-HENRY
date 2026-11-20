from ...contracts.spec import IndexSpec
from ...errors import IndexError


def validate_collection(collection, spec: IndexSpec) -> None:
    metadata = collection.metadata or {}
    if (metadata.get("dimension") != spec.dimension
            or metadata.get("embedding_fingerprint") != spec.embedding_fingerprint
            or collection.configuration["hnsw"]["space"] != spec.metric):
        raise IndexError("La colección Chroma es incompatible con el build.")
