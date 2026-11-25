"""Comparación por estrategia con la misma recuperación que usa la CLI."""

from dataclasses import asdict
from uuid import uuid4
from time import perf_counter
import json

from nubbix_assist.artifacts.validators import digest, file_digest
from nubbix_assist.bootstrap import language_model, local_embeddings
from nubbix_assist.generation.contracts.response import INSUFFICIENT
from nubbix_assist.generation.prompts import load_prompt
from nubbix_assist.llm.service import CallBudget
from nubbix_assist.query.service import answer_retrieval
from nubbix_assist.configuration.loader import load_config
from nubbix_assist.retrieval.service import Retriever
from nubbix_assist.retrieval.rrf import fuse
from nubbix_assist.timing import measure
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
    elapsed = perf_counter()
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
    setup_ms = {}
    with measure(setup_ms, "embedding_model_load"):
        model = local_embeddings(root)
    retrieval_config = load_config(root)["retrieval"]
    run_id = uuid4().hex
    directory = root / "runs" / run_id
    directory.mkdir(parents=True)
    report = {"run_id": run_id, "settings": config, "setup_ms": setup_ms, "strategies": {}}
    for build in builds:
        manifest = build.manifest
        retriever = Retriever(build, model, retrieval_config)
        rows = []
        for row in records:
            expected = row["expected_chunks"][manifest.strategy_fingerprint]
            timing = {}
            entry = {"question_id": row["question_id"], "expected_chunks": expected,
                     "answerable": row["answerable"], "timing_ms": timing,
                     "labels_reviewed": reviewed_for(row, [build])}
            rows.append(entry)
            start = perf_counter()
            try:
                with measure(timing, "retrieval_total"):
                    trace = retriever.retrieve(row["question"])
                timing.update(trace.timing_ms)
                if "vector_lookup" in timing:
                    timing["vector_with_embedding"] = timing["query_embedding"] + timing["vector_lookup"]
                ids = [s.chunk.chunk_id for s in trace.selected]
                lexical = [key for key, _ in trace.lexical_candidates]
                vector = [key for key, _ in trace.vector_candidates]
                candidates = trace.config["candidates"]
                ranks = {"bm25": lexical, "vector": vector, "rrf": [
                    key for key, _ in fuse([lexical, vector], trace.config["rrf_constant"], candidates)]}
                cuts = dict.fromkeys((trace.config["top_k"], candidates))
                entry["rankings"] = {name: {str(k): retrieval_metrics(ranked, expected, k) for k in cuts}
                                     for name, ranked in ranks.items()}
                entry.update(trace=asdict(trace), retrieved_ids=ids,
                             retrieval=retrieval_metrics(ids, expected, retriever.config["top_k"]))
            except (ValueError, RuntimeError, OSError) as error:
                entry["retrieval_error"] = str(error)
                continue
            if retrieval_only:
                continue
            try:
                with measure(timing, "generation"):
                    result = answer_retrieval(root, trace, generator, prompt)
                timing["query_total"] = timing["retrieval_total"] + timing["generation"]
                entry.update(answer=asdict(result.answer), query_run=result.run_id)
                if not row["answerable"]:
                    entry["correct_refusal"] = result.answer.system_answer == INSUFFICIENT
            except (ValueError, RuntimeError, OSError) as error:
                entry["generation_error"] = str(error)
                continue
            try:
                with measure(timing, "groundedness_judge"):
                    entry["judge"] = judge(result.answer, evaluator, judge_prompt)
            except (ValueError, RuntimeError, OSError) as error:
                entry["judge_error"] = str(error)
            finally:
                timing["eval_total"] = (perf_counter() - start) * 1000
        report["strategies"][manifest.strategy] = {"build": manifest.build_id, "summary": summarize(rows), "cases": rows}
    report["calls_used"] = budget.used
    report["run_wall_ms"] = (perf_counter() - elapsed) * 1000
    (directory / "eval.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
