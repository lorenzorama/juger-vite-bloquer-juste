import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.config import ROOT

RUNS_DIR = ROOT / "runs"


class RunLog:
    """Les events d'un run : en mémoire, dans runs/<run_id>.jsonl, et poussés aux listeners."""

    def __init__(self, run_id: str | None = None, directory: Path = RUNS_DIR) -> None:
        self.run_id = run_id or f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
        self.path = directory / f"{self.run_id}.jsonl"
        self.events: list[dict] = []
        self.listeners: list[Callable[[dict], None]] = []
        self._t0 = time.monotonic()

    def emit(self, type: str, **data) -> dict:
        event = {"run_id": self.run_id, "seq": len(self.events),
                 "t": round(time.monotonic() - self._t0, 3), "type": type, **data}
        self.events.append(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        for listener in self.listeners:
            listener(event)
        return event

    @staticmethod
    def read(path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
