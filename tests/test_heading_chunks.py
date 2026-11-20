"""Regresiones de trazabilidad del primer incremento de ingesta."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nubbix_assist.chunking.strategies.headings import chunk_by_headings
from nubbix_assist.chunking.validators import validate_chunks
from nubbix_assist.ingestion.markdown_loader import load_markdown
from nubbix_assist.ingestion.service import inspect_document


ROOT = Path(__file__).resolve().parents[1]
HR = Path("data/corpus/hr_policies.md")


class HeadingChunkTests(unittest.TestCase):
    def test_beneficios_trace_and_identity(self):
        chunks = inspect_document(HR, project_root=ROOT, strategy=chunk_by_headings)
        [benefits] = [chunk for chunk in chunks if chunk.section_paths == ("Beneficios",)]
        original = (ROOT / HR).read_bytes().decode("utf-8")
        expected_start = original.index("- Medicina prepaga:")
        self.assertEqual((benefits.start_char, benefits.end_char), (expected_start, len(original)))
        self.assertEqual(benefits.body, original[expected_start:])
        self.assertIn("USD 500", benefits.body)
        self.assertEqual(benefits.ordinal, 6)
        again = inspect_document(ROOT / HR, project_root=ROOT, strategy=chunk_by_headings)
        self.assertEqual(again, chunks)

    def test_unicode_crlf_and_fenced_heading(self):
        text = "# Guía\r\n\r\n## Uno\r\ná🙂\r\n```md\r\n## Ejemplo\r\n```\r\n\r\n## Dos\r\nfin"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "muestra.md"
            data = text.encode("utf-8")
            path.write_bytes(data)
            document = load_markdown(path, project_root=root)
            self.assertEqual(document.raw_text, text)
            self.assertEqual(document.source_sha256, sha256(data).hexdigest())
            first, last = inspect_document(path, project_root=root, strategy=chunk_by_headings)
            self.assertEqual(first.body, "á🙂\r\n```md\r\n## Ejemplo\r\n```\r\n\r\n")
            self.assertEqual(text[first.start_char:first.end_char], first.body)
            self.assertEqual(last.body, "fin")
            self.assertEqual(last.content, "Guía\nDos\n\nfin")
            path.write_bytes(data.replace(b"fin", b"FIN"))
            changed = inspect_document(path, project_root=root, strategy=chunk_by_headings)
            self.assertNotEqual(first.chunk_id, changed[0].chunk_id)

    def test_invalid_span_body_and_duplicate_id(self):
        document = load_markdown(HR, project_root=ROOT)
        chunks = chunk_by_headings(document)
        first = chunks[0]
        for invalid in ([replace(first, start_char=-1)], [replace(first, body="otro")], [first, first]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_chunks(document, invalid)
