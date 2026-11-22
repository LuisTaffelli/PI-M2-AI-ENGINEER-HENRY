from time import perf_counter

from nubbix_assist.artifacts.repository import Build
from nubbix_assist.embeddings.contracts.inputs import TextInput
from nubbix_assist.lexical.search import search
from .contracts.candidates import Retrieval, Selected
from .rrf import fuse
from .rewrite import QueryRewriter


class Retriever:
    def __init__(self, build: Build, embeddings, config: dict, *, reranker=None, multi_query=False):
        if embeddings.spec != build.manifest.embeddings:
            raise ValueError("El modelo de consulta es incompatible con el build.")
        self.build = build
        self.embeddings = embeddings
        self.config = dict(config)
        self.reranker = reranker
        self.rewriter = QueryRewriter(build.lexical.idf) if multi_query else None

    def retrieve(self, question: str, *, source: str | None = None) -> Retrieval:
        """Busca evidencia para `question` en el índice, opcionalmente limitada al documento `source`.

        Conserva las ramas de la pregunta original y registra las etapas opcionales en details.
        """
        if not question.strip():
            raise ValueError("La pregunta está vacía.")
        start = perf_counter()
        top_k = self.config["top_k"]
        allowed = {key for key, chunk in self.build.catalog.items() if source is None or chunk.source == source}
        limit = min(len(allowed), self.config["candidates"])
        queries = [question]
        if self.rewriter:
            queries.extend(self.rewriter.variants(question))
        inputs = [TextInput(str(i), query) for i, query in enumerate(queries)]
        encoded = self.embeddings.encode(inputs, "query") if limit else []
        rankings = []
        constant = self.config["rrf_constant"]
        for index, query in enumerate(queries):
            lexical = search(self.build.lexical, query, limit, allowed)
            hits = self.build.vectors.search(encoded[index].vector, limit, source) if limit else []
            vectors = [(hit.id, hit.distance) for hit in hits]
            if any(key not in allowed for key, _ in vectors):
                raise ValueError("Chroma devolvió un ID fuera del catálogo o filtro.")
            if index == 0:
                original_vectors, original_lexical = vectors, lexical
            ranks = [[key for key, _ in branch] for branch in (lexical, vectors)]
            rankings.append(fuse(ranks, constant, limit))
        pool = rankings[0]
        details = {}
        if self.rewriter:
            query_ranks = [[key for key, _ in ranking] for ranking in rankings]
            details["query_rankings"] = dict(zip(queries, query_ranks, strict=True))
            if len(queries) > 1:
                pool = fuse(query_ranks, constant, limit)
        if self.reranker and pool:
            chunks = [self.build.catalog[key] for key, _ in pool]
            values = self.reranker.score(question, chunks)
            scores = dict(zip((chunk.chunk_id for chunk in chunks), values, strict=True))
            details["reranking"] = {"model": self.reranker.model_id, "revision": self.reranker.revision,
                                    "pool_rrf": pool, "scores": scores}
            pool = sorted(pool, key=lambda pair: scores[pair[0]], reverse=True)
        selected = [Selected(self.build.catalog[key], score) for key, score in pool[:top_k]]
        return Retrieval(question, self.build.manifest.build_id, {**self.config, "source": source},
                         original_vectors, original_lexical, selected, (perf_counter() - start) * 1000,
                         ["Menos candidatos que top_k."] if len(selected) < top_k else [], details)
