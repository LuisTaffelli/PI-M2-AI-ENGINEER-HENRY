from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from unittest import TestCase

from nubbix_assist.bootstrap import inspect_heading_document
from nubbix_assist.generation.citations import resolve
from nubbix_assist.ingestion.revisions import register_version
from nubbix_assist.retrieval.contracts.candidates import Selected
from nubbix_assist.ui.reader import render_result


class DocumentVersionTests(TestCase):
    def setUp(self):
        repo = Path(__file__).resolve().parents[1]
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = Path("data/corpus/it_manual.md")
        shutil.copytree(repo / "data/corpus", self.root / "data/corpus")
        shutil.copytree(repo / "docs/fuentes", self.root / "docs/fuentes")
        self.edited = self.root / "edicion.md"
        self.edited.write_text("# Manual actualizado\n\n## Hardware\nContenido de prueba.\n", encoding="utf-8")

    def test_manual_labels_retries_and_historical_citations(self):
        original = inspect_heading_document(self.source, project_root=self.root)[0]
        labels = ["1.10", "1.2", "Versión N"]
        ids = set()
        for label in labels:
            entry = register_version(self.root, self.source, self.edited, label)
            self.assertEqual(register_version(self.root, self.source, self.edited, label), entry)
            current = inspect_heading_document(self.source, project_root=self.root)[0]
            self.assertEqual(current.version, label)
            self.assertEqual(current.source, self.source.as_posix())
            ids.add(current.chunk_id)
        self.assertEqual(len(ids), len(labels))
        older = inspect_heading_document(self.source, project_root=self.root, version="1.10")[0]
        self.assertEqual(resolve([older.chunk_id], [Selected(older, .5)])[0].version, "1.10")
        self.assertIn("Versión 1.10", render_result(self.root, "", [older]))
        self.assertIn("Versión 1 · Cita", render_result(self.root, "", [original]))
        self.edited.write_text("# Manual\n## Hardware\nOtro texto.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "otro contenido"):
            register_version(self.root, self.source, self.edited, "1.10")
        with self.assertRaisesRegex(ValueError, "desconocida"):
            inspect_heading_document(self.source, project_root=self.root, version="4")

    def test_concurrent_registrations_keep_both_labels_and_detect_tampering(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            entries = list(pool.map(lambda label: register_version(self.root, self.source, self.edited, label),
                                    ["2", "Edición mayo"]))
        self.assertEqual(len(set(entries)), 2)
        (entries[0] / "document.md").write_text("# Manual\n## Otro\nCambio.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cambió en disco"):
            inspect_heading_document(self.source, project_root=self.root, version="2")
