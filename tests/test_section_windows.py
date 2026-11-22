from types import SimpleNamespace
from unittest import TestCase

from evals.contracts.golden import reviewed_for
from nubbix_assist.bootstrap import STRATEGIES
from nubbix_assist.chunking.validators import validate_chunks
from nubbix_assist.ingestion.contracts import Document


class SectionWindowTests(TestCase):
    def test_windows_reset_at_h2_and_preserve_offsets_and_overlap(self):
        words = [f"término{i}" for i in range(81)]
        text = "# Manual\r\n## Viajes\r\n" + " ".join(words) + "\r\n## Cursos\r\n" + " ".join(words[:80])
        document = Document("manual.md", "Manual", "prueba", text)
        chunks = STRATEGIES["section_words_v1"](document)
        validate_chunks(document, chunks)
        self.assertEqual([chunk.body.split() for chunk in chunks], [words[:80], words[60:], words[:80]])
        self.assertEqual([chunk.section_paths for chunk in chunks], [("Viajes",), ("Viajes",), ("Cursos",)])
        for chunk in chunks:
            self.assertEqual(chunk.content, f"Manual\n{chunk.section_paths[0]}\n\n{chunk.body}")

    def test_review_only_applies_to_confirmed_strategies(self):
        builds = [SimpleNamespace(manifest=SimpleNamespace(strategy_fingerprint=name))
                  for name in ("sections", "windows", "combined")]
        row = {"labeling_status": "reviewed", "expected_chunks": {"sections": [], "windows": []}}
        self.assertTrue(reviewed_for(row, builds[:2]))
        row["reviewed_strategies"] = ["sections", "windows"]
        row["expected_chunks"]["combined"] = []
        self.assertTrue(reviewed_for(row, builds[:2]))
        self.assertFalse(reviewed_for(row, builds))
        row["reviewed_strategies"].append("combined")
        self.assertTrue(reviewed_for(row, builds))
