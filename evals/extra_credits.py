"""Comparación pareada de recuperación. Ejecutar desde la raíz del PI."""
import argparse
import csv
import json
from pathlib import Path
import platform
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from evals.contracts.golden import load_golden
from evals.metrics import latency_summary, retrieval_metrics
from nubbix_assist.artifacts.validators import file_digest
from nubbix_assist.bootstrap import load_build, local_embeddings
from nubbix_assist.configuration.loader import load_config
from nubbix_assist.retrieval.rerank import LocalReranker
from nubbix_assist.retrieval.service import Retriever


def measure(build, embeddings, reranker, config, golden, informal, repeats):
    engines = {
        "base": Retriever(build, embeddings, config),
        "multi": Retriever(build, embeddings, config, multi_query=True),
        "rerank": Retriever(build, embeddings, config, reranker=reranker),
    }
    for engine in engines.values():
        engine.retrieve(golden[0]["question"])
    rows, summaries = [], []
    for dataset in ("original", "informal"):
        modes = list(engines) if dataset == "original" else ["base", "multi"]
        latency = {mode: [] for mode in modes}
        for index, case in enumerate(golden):
            qid = case["question_id"]
            query = case["question"] if dataset == "original" else informal[qid]
            expected = set(case["expected_chunks"][build.manifest.strategy_fingerprint])
            ids, variants = {}, {}
            for repeat in range(repeats):
                offset = (index + repeat) % len(modes)
                for mode in modes[offset:] + modes[:offset]:
                    trace = engines[mode].retrieve(query)
                    ranking = [item.chunk.chunk_id for item in trace.selected]
                    if mode in ids and ranking != ids[mode]:
                        raise ValueError(f"Ranking inestable en {qid}, {mode}.")
                    ids[mode] = ranking
                    variants[mode] = list(trace.details.get("query_rankings", {}))[1:]
                    latency[mode].append({"retrieval_total": trace.elapsed_ms, **trace.timing_ms})
                    if mode == "rerank":
                        pool = [key for key, _ in trace.details["reranking"]["pool_rrf"]]
                if "rerank" in modes and pool[:config["top_k"]] != ids["base"]:
                    raise ValueError("El re-ranking partió de otra selección de candidatos.")
            for mode in modes:
                metrics = retrieval_metrics(ids[mode], expected, config["top_k"]) or {}
                rows.append(dict(strategy=build.manifest.strategy, dataset=dataset, mode=mode, id=qid,
                                 question=query, variants=variants[mode], selected=ids[mode],
                                 precision=metrics.get("precision_at_k"), recall=metrics.get("recall_at_k"),
                                 hit1=int(bool(ids[mode]) and ids[mode][0] in expected) if expected else None,
                                 rr_at_k=metrics.get("rr_at_k")))
        for mode in modes:
            scored = [r for r in rows if r["dataset"] == dataset and r["mode"] == mode and r["recall"] is not None]
            timings = latency_summary(latency[mode])
            total = timings["retrieval_total"]
            summaries.append(dict(strategy=build.manifest.strategy, dataset=dataset, mode=mode,
                                  scored=len(scored), precision=mean(r["precision"] for r in scored),
                                  recall=mean(r["recall"] for r in scored), hit1=sum(r["hit1"] for r in scored),
                                  mrr_at_k=mean(r["rr_at_k"] for r in scored),
                                  median_ms=round(total["median_ms"], 2), p95_ms=round(total["p95_ms"], 2),
                                  timings_ms=timings))
    return rows, summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builds", nargs=2, required=True, metavar="BUILD")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "runs/extra-credits")
    args = parser.parse_args()
    if args.repeats < 1 or args.threads < 1:
        parser.error("Se requiere al menos una repetición y un hilo.")
    import torch
    torch.set_num_threads(args.threads)
    builds = [load_build(ROOT, bid) for bid in args.builds]
    gold_path, informal_path = ROOT / "evals/dataset.jsonl", ROOT / "evals/preguntas_informales.json"
    golden = load_golden(gold_path, ROOT, builds, require_review=True)
    informal = json.loads(informal_path.read_text())
    if set(informal) != {row["question_id"] for row in golden} or not all(
        isinstance(query, str) and query.strip() for query in informal.values()
    ):
        raise ValueError("Las consultas informales deben corresponder al golden.")
    embeddings, reranker = local_embeddings(ROOT), LocalReranker()
    config = load_config(ROOT)["retrieval"]
    rows, summary = [], []
    for build in builds:
        result, metrics = measure(build, embeddings, reranker, config, golden, informal, args.repeats)
        rows.extend(result)
        summary.extend(metrics)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "preguntas.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "variants": json.dumps(row["variants"], ensure_ascii=False),
                             "selected": json.dumps(row["selected"])})
    metadata = dict(builds=args.builds, retrieval=config, reranker=reranker.model_id, revision=reranker.revision,
                    golden_sha256=file_digest(gold_path), informal_sha256=file_digest(informal_path),
                    device="cpu", platform=platform.machine(), torch=str(torch.__version__),
                    threads=args.threads, repeats=args.repeats, results=summary)
    (args.output / "resumen.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
