"""Comparación por estrategia con la misma recuperación que usa la CLI."""

from dataclasses import asdict
from uuid import uuid4
import json

from nubbix_assist.artifacts.validators import digest, file_digest
from nubbix_assist.bootstrap import language_model, local_embeddings
from nubbix_assist.generation.contracts.response import INSUFFICIENT
from nubbix_assist.generation.prompts import load_prompt
from nubbix_assist.llm.service import CallBudget
from nubbix_assist.query.service import answer_retrieval
from nubbix_assist.configuration.loader import load_config
from nubbix_assist.retrieval.service import Retriever
from .contracts.golden import reviewed_for
from .groundedness.judge import judge
from .metrics import retrieval_metrics, summarize


def evaluate(root, builds, dataset, records, *, retrieval_only, max_calls):
    """Evalúa los índices de `builds` con los registros de `dataset` recibidos en `records`.

    Con `retrieval_only` mide la búsqueda local. La evaluación completa comparte
    `max_calls` entre generación y juez. Devuelve el informe por estrategia y
    lo guarda en `runs/` bajo `root`.
    """
    budget = CallBudget(max_calls)
    reviewed = sum(reviewed_for(row, builds) for row in records)
    config = {"max_calls": max_calls, "mode": "retrieval" if retrieval_only else "full",
              "label_review": {"reviewed": reviewed, "pending": len(records) - reviewed},
              "config_sha256": file_digest(root / "config.yaml"), "dataset_sha256": file_digest(dataset)}
    if not retrieval_only:
        generator = language_model(root, "GENERATOR", budget)
        evaluator = language_model(root, "JUDGE", budget)
        prompt, judge_prompt = (load_prompt(root, name) for name in ("generation", "groundedness"))
        config.update(generator=[generator.provider.name, generator.provider.model],
                      judge=[evaluator.provider.name, evaluator.provider.model],
                      prompt_hashes=[digest(prompt), digest(judge_prompt)])
    model = local_embeddings(root)
    retrieval_config = load_config(root)["retrieval"]
    run_id = uuid4().hex
    directory = root / "runs" / run_id
    directory.mkdir(parents=True)
    report = {"run_id": run_id, "settings": config, "strategies": {}}
    for build in builds:
        manifest = build.manifest
        retriever = Retriever(build, model, retrieval_config)
        rows = []
        for row in records:
            expected = row["expected_chunks"][manifest.strategy_fingerprint]
            entry = {"question_id": row["question_id"], "expected_chunks": expected,
                     "labels_reviewed": reviewed_for(row, [build])}
            rows.append(entry)
            try:
                trace = retriever.retrieve(row["question"])
                ids = [s.chunk.chunk_id for s in trace.selected]
                entry.update(trace=asdict(trace), retrieved_ids=ids,
                             retrieval=retrieval_metrics(ids, expected, retriever.config["top_k"]))
            except (ValueError, RuntimeError, OSError) as error:
                entry["retrieval_error"] = str(error)
                continue
            if retrieval_only:
                continue
            try:
                result = answer_retrieval(root, trace, generator, prompt)
                entry.update(answer=asdict(result.answer), query_run=result.run_id)
                if not row["answerable"]:
                    entry["correct_refusal"] = result.answer.system_answer == INSUFFICIENT
            except (ValueError, RuntimeError, OSError) as error:
                entry["generation_error"] = str(error)
                continue
            try:
                entry["judge"] = judge(result.answer, evaluator, judge_prompt)
            except (ValueError, RuntimeError, OSError) as error:
                entry["judge_error"] = str(error)
        report["strategies"][manifest.strategy] = {"build": manifest.build_id, "summary": summarize(rows), "cases": rows}
    report["calls_used"] = budget.used
    (directory / "eval.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
