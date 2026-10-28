"""uv run python -m app.cli --config B "Réponds aux nouveaux mails." """

import argparse
import asyncio

from app.agent import run_agent
from app.events import RunLog


def show(event: dict) -> None:
    t, kind = f"[{event['t']:5.1f}s]", event["type"]
    if kind == "tool_call":
        print(f"{t} → {event['tool']}({event['args']})")
    elif kind == "jev_verdict":
        scores = " ".join(f"{k}={v:.2f}" for k, v in event["scores"].items())
        mode = "enforced" if event["applied"] else "shadow"
        print(f"{t}   {event['point']} [{mode}] {event['decision']} {scores} "
              f"({event['latency_ms']} ms) — {event['reason']}")
    elif kind == "draft_created":
        flag = "  ⚠ Jev aurait bloqué" if event["would_block"] else ""
        print(f"{t}   ✉ brouillon pour {event['to']}{flag}\n        {event['body']!r}")
    elif kind == "draft_blocked":
        print(f"{t}   ⛔ brouillon bloqué pour {event['to']} ({event['reason']})")
    elif kind in {"run_started", "run_finished", "error"}:
        details = {k: v for k, v in event.items() if k not in {"run_id", "seq", "t", "type"}}
        print(f"{t} {kind} {details}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("instruction", nargs="?", default="Réponds aux nouveaux mails.")
    parser.add_argument("--config", choices=["A", "B"], default="A")
    parser.add_argument("--mailbox", default="demo")
    args = parser.parse_args()
    log = RunLog()
    log.listeners.append(show)
    asyncio.run(run_agent(args.config, args.mailbox, args.instruction, log))
    print(f"Log : {log.path}")


if __name__ == "__main__":
    main()
