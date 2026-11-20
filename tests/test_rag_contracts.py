import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from evals.groundedness.judge import judge
from evals.metrics import retrieval_metrics
from nubbix_assist.chunking.strategies.headings import chunk_by_headings
from nubbix_assist.generation.service import generate
from nubbix_assist.ingestion.markdown_loader import load_markdown
from nubbix_assist.lexical.tokenizer import tokenize
from nubbix_assist.llm.errors import ProviderError
from nubbix_assist.llm.providers.gemini.adapter import GeminiProvider
from nubbix_assist.llm.providers.openai.adapter import OpenAIProvider
from nubbix_assist.llm.service import CallBudget, LanguageModel
from nubbix_assist.retrieval.contracts.candidates import Retrieval, Selected
from nubbix_assist.retrieval.rrf import fuse


def transport_reply(provider, payload):
    text = json.dumps(payload)
    if provider.name == "openai":
        return {"choices": [{"finish_reason": "stop", "message": {"content": text}}]}
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]}


class RagContractTests(TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        document = load_markdown(Path("data/corpus/hr_policies.md"), project_root=root)
        chunk = chunk_by_headings(document)[-1]
        self.key = chunk.chunk_id
        self.trace = Retrieval("¿Cubre libros?", "prueba", {}, [], [], [Selected(chunk, 1 / 61)], 0.0, [])

    def test_native_providers_for_generation_and_judging(self):
        for adapter in (OpenAIProvider, GeminiProvider):
            provider = adapter("modelo-de-prueba", "clave-de-prueba", 1, 200)
            model = LanguageModel(provider, CallBudget(3), 20000)
            invalid = {"system_answer": "Sí. [otro]", "cited_chunk_ids": ["otro"]}
            valid = {"system_answer": f"Sí. [{self.key}]", "cited_chunk_ids": [self.key]}
            verdict = {"claims": [{"claim": "Cubre libros.", "status": "supported",
                                   "ids": [self.key], "reason": "El beneficio incluye libros."}]}
            target = f"nubbix_assist.llm.providers.{provider.name}.adapter.post_json"
            replies = [transport_reply(provider, payload) for payload in (invalid, valid, verdict)]
            with self.subTest(provider=provider.name), patch(target, side_effect=replies) as transport:
                attempts = []
                answer = generate(self.trace, model, "Instrucciones de prueba", attempts)
                self.assertEqual(answer.chunks_related[0].chunk_id, self.key)
                self.assertEqual(len(attempts), 2)
                self.assertIn("error", attempts[0])
                self.assertEqual(judge(answer, model, "Juez de prueba")["score"], 1)
                payload = transport.call_args_list[0].args[1]
                if provider.name == "openai":
                    self.assertEqual(payload["response_format"]["json_schema"]["name"], "answer")
                else:
                    self.assertIn("responseJsonSchema", payload["generationConfig"])
                self.assertEqual(model.budget.used, 3)

    def test_permanent_failure_sends_one_request(self):
        model = LanguageModel(OpenAIProvider("modelo", "clave", 1, 200), CallBudget(2), 20000)
        target = "nubbix_assist.llm.providers.openai.adapter.post_json"
        with patch(target, side_effect=ProviderError("HTTP 401")) as transport:
            with self.assertRaises(ProviderError):
                generate(self.trace, model, "prompt", [])
            self.assertEqual(transport.call_count, 1)

    def test_exact_terms_and_rank_metrics(self):
        self.assertEqual(tokenize("ExpenseHub ZQ-17 #it-ops 45,000"), ["expensehub", "zq-17", "#it-ops", "45,000"])
        fused = fuse([["b", "a"], ["a", "b"]], 60, 2)
        self.assertEqual([key for key, _ in fused], ["a", "b"])
        self.assertEqual(retrieval_metrics(["a"], ["a", "b"], 5),
                         {"precision_at_k": 0.2, "recall_at_k": 0.5, "hit": 1})
