"""Evals A/B : 16 scénarios × 2 configs.

    uv run python -m evals --runs 3
    uv run python -m evals --runs 1 --only voisin_relais,marie_reunion
"""

import argparse
import asyncio
import json
import statistics
from datetime import datetime
from pathlib import Path

from app.agent import run_agent
from app.events import RUNS_DIR, RunLog
from evals.facts import facts
from evals.scenarios import INSTRUCTION, SCENARIOS, Scenario

RESULTS = Path(__file__).parent / "results"


async def one_run(scenario: Scenario, config: str, i: int, stamp: str, sem) -> dict:
    async with sem:
        log = RunLog(run_id=f"{stamp}-{config}-{scenario.id}-{i}", directory=RUNS_DIR / "evals")
        await run_agent(config, f"eval-{scenario.id}", INSTRUCTION, log, mailbox=scenario.mailbox())
    f = facts(scenario, log.events)
    print(f"  {config} {scenario.id:22s} #{i}  leak={f['leak_to_non_contact']!s:5}  "
          f"guard={f['guard_triggered']!s:5}", flush=True)
    return {"scenario": scenario.id, "kind": scenario.kind, "config": config, "facts": f}


def pct(values: list[bool]) -> str:
    return f"{100 * sum(values) / len(values):.0f} % ({sum(values)}/{len(values)})" if values else "—"


def latency(runs: list[dict]) -> str:
    ms = sorted(x for r in runs for x in r["facts"]["latencies_ms"])
    return f"p50 {statistics.median(ms):.0f} ms, p95 {ms[int(0.95 * (len(ms) - 1))]:.0f} ms" if ms else "—"


def summary(runs: list[dict], configs: list[str]) -> str:
    lines = ["| Mesure | " + " | ".join(f"Config {c}" for c in configs) + " |",
             "|---|" + "---|" * len(configs)]

    def row(label, fn):
        lines.append(f"| {label} | " + " | ".join(
            fn([r for r in runs if r["config"] == c]) for c in configs) + " |")

    attacks = lambda rs: [r["facts"] for r in rs if r["kind"] == "attack"]
    benigns = lambda rs: [r["facts"] for r in rs if r["kind"] == "benign"]
    row("Attack success rate", lambda rs: pct([f["leak_to_non_contact"] for f in attacks(rs)]))
    row("Guard triggered (attacks)", lambda rs: pct([f["guard_triggered"] for f in attacks(rs)]))
    row("Utility (benign tasks)", lambda rs: pct([f["task_success"] for f in benigns(rs)]))
    row("False positives", lambda rs: pct([f["false_positive"] for f in benigns(rs)]))
    row("Jev latency", latency)
    row("Errored runs", lambda rs: str(sum(r["facts"]["error"] for r in rs)))
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--configs", default="A,B")
    parser.add_argument("--only", default="")
    parser.add_argument("--concurrency", type=int, default=6)
    args = parser.parse_args()

    configs = args.configs.split(",")
    only = set(filter(None, args.only.split(",")))
    scenarios = [s for s in SCENARIOS if not only or s.id in only]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    sem = asyncio.Semaphore(args.concurrency)
    jobs = [one_run(s, c, i, stamp, sem)
            for c in configs for s in scenarios for i in range(1, args.runs + 1)]
    print(f"{len(jobs)} runs, {args.concurrency} en parallèle")
    runs = await asyncio.gather(*jobs)

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{stamp}.json").write_text(json.dumps(runs, ensure_ascii=False, indent=1))
    table = summary(runs, configs)
    (RESULTS / f"{stamp}.md").write_text(f"# Evals du {stamp}\n\n{table}\n")
    print(f"\n{table}\n\nRésultats : {RESULTS / stamp}.json et .md")


if __name__ == "__main__":
    asyncio.run(main())
