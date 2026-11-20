from time import perf_counter

from nubbix_assist.artifacts.repository import Build
from nubbix_assist.embeddings.contracts.inputs import TextInput
from nubbix_assist.lexical.search import search
from .contracts.candidates import Retrieval, Selected
from .rrf import fuse


class Retriever:
    def __init__(self, build: Build, embeddings, config: dict):
        if embeddings.spec != build.manifest.embeddings:
            raise ValueError("El modelo de consulta es incompatible con el build.")
        self.build = build
        self.embeddings = embeddings
        self.config = dict(config)

    def retrieve(self, question: str, *, source: str | None = None) -> Retrieval:
        if not question.strip():
            raise ValueError("La pregunta está vacía.")
        start = perf_counter()
        top_k = self.config["top_k"]
        allowed = {key for key, chunk in self.build.catalog.items() if source is None or chunk.source == source}
        limit = min(len(allowed), self.config["candidates"])
        lexical = search(self.build.lexical, question, limit, allowed)
        vectors = []
        if limit:
            vector = self.embeddings.encode([TextInput("question", question)], "query")[0].vector
            hits = self.build.vectors.search(vector, limit, source)
            vectors = [(hit.id, hit.distance) for hit in hits]
            if any(key not in allowed for key, _ in vectors):
                raise ValueError("Chroma devolvió un ID fuera del catálogo o filtro.")
        fused = fuse([[key for key, _ in branch] for branch in (lexical, vectors)], self.config["rrf_constant"], top_k)
        selected = [Selected(self.build.catalog[key], score) for key, score in fused]
        return Retrieval(question, self.build.manifest.build_id, {**self.config, "source": source},
                         vectors, lexical, selected, (perf_counter() - start) * 1000,
                         ["Menos candidatos que top_k."] if len(selected) < top_k else [])
