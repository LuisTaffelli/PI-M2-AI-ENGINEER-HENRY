import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from evals.metrics import latency_summary, retrieval_metrics, summarize
from evals.suite import evaluate
from nubbix_assist.bootstrap import inspect_heading_document
from nubbix_assist.generation.contracts.response import INSUFFICIENT
from nubbix_assist.lexical.index import BM25Index
from nubbix_assist.llm.contracts.outputs import Completion
from nubbix_assist.llm.service import LanguageModel


class EvalObservabilityTests(TestCase):
    def test_rr_counts_first_match_zero_or_not_applicable(self):
        cases = [retrieval_metrics(["z", "a", "b"], ["a", "b"], 2),
                 retrieval_metrics(["z", "a"], ["a"], 1),
                 retrieval_metrics(["a"], [], 1)]
        self.assertEqual([case["rr_at_k"] if case else None for case in cases], [.5, 0, None])
        self.assertEqual(summarize([{"retrieval": case} for case in cases])["retrieval_macro"]["mrr_at_k"], .25)

    def test_latency_summary_counts_only_observed_samples(self):
        result = latency_summary([{"x": 2}, {"x": 1, "y": 7}, {"x": 9}, {}])
        self.assertEqual(result, {"x": {"n": 3, "median_ms": 2, "p95_ms": 9},
                                  "y": {"n": 1, "median_ms": 7, "p95_ms": 7}})

    def test_refusal_denominator_separates_success_error_and_not_run(self):
        rows = [{"answerable": False, "correct_refusal": v} for v in (True, False)]
        rows += [{"answerable": False, "generation_error": "simulado"}, {"answerable": False}]
        report = summarize(rows)
        self.assertEqual(report["out_of_scope_expected"], 4)
        self.assertEqual(report["out_of_scope_answered"], 2)
        self.assertEqual(report["out_of_scope_correct"], 1)
        self.assertEqual(report["out_of_scope_errors"], 1)
        self.assertEqual(report["out_of_scope_not_run"], 1)
        self.assertEqual(report["correct_refusal_rate"], .5)
        unmeasured = summarize([{"answerable": False, "retrieval": None}])
        self.assertIsNone(unmeasured["correct_refusal_rate"])
        self.assertEqual(unmeasured["out_of_scope_not_run"], 1)

    def test_full_runner_records_real_stages_with_fake_provider(self):
        project = Path(__file__).resolve().parents[1]
        chunks = inspect_heading_document(Path("data/corpus/hr_policies.md"), project_root=project, version="1")
        chunk = chunks[-1]
        embedding = SimpleNamespace(spec="fake",
                                    encode=lambda rows, role: [SimpleNamespace(vector=[1.]) for _ in rows])
        build = SimpleNamespace(manifest=SimpleNamespace(embeddings="fake", strategy="demo",
                                                         strategy_fingerprint="fp", build_id="demo"),
                                catalog={c.chunk_id: c for c in chunks}, lexical=BM25Index.build(chunks),
                                vectors=Mock())
        build.vectors.search.return_value = [SimpleNamespace(id=chunk.chunk_id, distance=0.)]
        rows = [dict(question_id="q01", question="¿Cubre libros?", answerable=True,
                     expected_chunks={"fp": [chunk.chunk_id]}, labeling_status="reviewed"),
                dict(question_id="q02", question="¿Cómo llego a Marte?", answerable=False,
                     expected_chunks={"fp": []}, labeling_status="reviewed")]
        completions = iter([
            {"system_answer": f"Cubre libros. [{chunk.chunk_id}]", "cited_chunk_ids": [chunk.chunk_id]},
            {"claims": [{"claim": "Cubre libros", "status": "supported", "reason": "Está escrito",
                         "ids": [chunk.chunk_id]}]},
            {"system_answer": INSUFFICIENT, "cited_chunk_ids": []},
            {"claims": []},
        ])

        def local_provider(root, role, budget):
            fake = SimpleNamespace(name="determinista", model=role,
                                   complete=lambda request: Completion(json.dumps(next(completions)), {}, "stop"))
            return LanguageModel(fake, budget, 50_000)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.yaml").write_bytes((project / "config.yaml").read_bytes())
            dataset = root / "golden.jsonl"
            dataset.write_text("\n".join(map(json.dumps, rows)))
            with patch("evals.suite.local_embeddings", return_value=embedding), \
                    patch("evals.suite.language_model", side_effect=local_provider), \
                    patch("evals.suite.load_prompt", return_value="Prompt de prueba"):
                report = evaluate(root, [build], dataset, rows, retrieval_only=False, max_calls=4)
            self.assertEqual(report["calls_used"], 4)
            strategy = report["strategies"]["demo"]
            metrics = strategy["summary"]
            self.assertEqual(metrics["out_of_scope_correct"], 1)
            self.assertEqual(metrics["rankings_macro"]["vector"]["5"]["mrr_at_k"], 1.)
            self.assertEqual(metrics["rankings_macro"]["rrf"]["10"]["n"], 1)
            for stage in ("query_embedding", "bm25", "vector_lookup", "rrf", "retrieval_total",
                          "generation", "groundedness_judge", "query_total", "eval_total"):
                self.assertEqual(metrics["timings_ms"][stage]["n"], 2, stage)
            query = root / "runs" / strategy["cases"][0]["query_run"] / "query.json"
            self.assertGreaterEqual(json.loads(query.read_text())["attempts"][0]["model_ms"], 0.)
