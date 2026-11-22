import csv
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from nubbix_assist.bootstrap import inspect_heading_document
from nubbix_assist.lexical.index import BM25Index
from nubbix_assist.retrieval.rewrite import QueryRewriter
from nubbix_assist.retrieval.service import Retriever
from nubbix_assist.ui.examples import load_examples
from nubbix_assist.ui.reader import render_result


class ExtraCreditsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.chunks = inspect_heading_document(Path("data/corpus/hr_policies.md"), project_root=cls.root, version="1")
        cls.build = SimpleNamespace(manifest=SimpleNamespace(embeddings="test", build_id="prueba"),
                                    catalog={c.chunk_id: c for c in cls.chunks},
                                    vectors=Mock(), lexical=BM25Index.build(cls.chunks))
        cls.build.vectors.search.return_value = [SimpleNamespace(id=c.chunk_id, distance=i / 10)
                                                 for i, c in enumerate(cls.chunks)]
        cls.embeddings = Mock(spec=["encode"])
        cls.embeddings.spec = "test"
        cls.embeddings.encode.side_effect = lambda items, role: [SimpleNamespace(vector=[1.0]) for _ in items]

    def test_rewrite_preserves_identifiers_negation_and_amounts(self):
        rewrite = QueryRewriter(["factura", "compra", "curso"])
        query = "no pagar USD 3000 por la facutra de #prod"
        self.assertEqual(rewrite.variants(query), ["no pagar USD 3000 por la factura de #prod"])
        self.assertEqual(rewrite.variants("curso"), [])

    def test_rerank_uses_same_pool_preserves_rrf_and_handles_empty_filter(self):
        config = {"top_k": 2, "candidates": 6, "rrf_constant": 60}
        base = Retriever(self.build, self.embeddings, config).retrieve("vacaciones")
        scorer = Mock(model_id="scorer", revision="rev")
        scorer.score.side_effect = lambda question, chunks: list(range(len(chunks)))
        engine = Retriever(self.build, self.embeddings, config, reranker=scorer)
        ranked = engine.retrieve("vacaciones")
        pool = ranked.details["reranking"]["pool_rrf"]
        self.assertEqual(pool[:2], [(i.chunk.chunk_id, i.score) for i in base.selected])
        self.assertEqual([(i.chunk.chunk_id, i.score) for i in ranked.selected], list(reversed(pool))[:2])
        self.assertFalse(engine.retrieve("vacaciones", source="ausente").selected)
        self.assertEqual(scorer.score.call_count, 1)

    def test_duplicate_queries_do_not_add_votes(self):
        config = {"top_k": 2, "candidates": 6, "rrf_constant": 60}
        baseline = Retriever(self.build, self.embeddings, config).retrieve("vacaciones")
        expanded = Retriever(self.build, self.embeddings, config, multi_query=True).retrieve("vacaciones")
        self.assertEqual(baseline.selected, expanded.selected)
        self.assertEqual(list(expanded.details["query_rankings"]), ["vacaciones"])

    def test_reader_links_only_cited_passages_and_escapes_model_text(self):
        chunk = self.chunks[0]
        content = render_result(self.root, f"<script> [{chunk.chunk_id}]", [chunk])
        self.assertNotIn("<script>", content)
        self.assertIn(f'href="#pasaje-{chunk.chunk_id}"', content)
        self.assertIn(f'id="pasaje-{chunk.chunk_id}"', content)
        self.assertNotIn("source-link", render_result(self.root, "Evidencia insuficiente", []))

    def test_all_saved_versions_render_the_recorded_answer_and_sources(self):
        folder = self.root / "evals/resultados"
        saved = load_examples(self.root)
        with (folder / "2026-11-22-generacion-golden-revisado.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(saved), len({row["pregunta_id"] for row in rows}))
        self.assertEqual(sum(len(item.versions) for item in saved.values()), len(rows) + 1)
        for row in rows:
            item = saved[row["pregunta_id"]]
            text, chunks = item.versions[row["estrategia"]]
            self.assertEqual((item.question, text), (row["pregunta"], row["respuesta"]))
            self.assertEqual({c.source for c in chunks}, set(filter(None, row["fuentes_citadas"].split(" | "))))
            html = render_result(self.root, text, chunks)
            self.assertEqual(html.count('class="source-view"'), len(chunks))
            for chunk in chunks:
                self.assertIn(f'href="#pasaje-{chunk.chunk_id}"', html)
        pilot = json.loads((folder / "2026-11-22-ejemplo-q09.json").read_text())
        text, chunks = saved["q09"].versions["pilot"]
        self.assertEqual(text, pilot["system_answer"])
        self.assertEqual([c.chunk_id for c in chunks], [c["chunk_id"] for c in pilot["chunks_related"]])
