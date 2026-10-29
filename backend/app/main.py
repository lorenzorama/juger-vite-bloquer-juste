import asyncio
import json
import re
import shutil
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from app import agent
from app.config import ROOT, get_settings
from app.events import RunLog
from app.mailbox import FIXTURES, LocalMailbox

app = FastAPI(title="Agent mail protégé par Jev")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])

RUNS: dict[str, RunLog] = {}
_TASKS: set[asyncio.Task] = set()
REPLAYS_DIR = ROOT / "replays"
REPLAY_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")


class RunRequest(BaseModel):
    instruction: str = "Réponds aux nouveaux mails."
    config: Literal["A", "B"] = "A"
    mailbox: str = "demo"


class SaveRequest(BaseModel):
    name: str


def _mailboxes() -> list[str]:
    return sorted(p.stem for p in FIXTURES.glob("*.json") if not p.name.endswith(".contacts.json"))


def _load(mailbox: str) -> LocalMailbox:
    if mailbox not in _mailboxes():
        raise HTTPException(404, f"Boîte inconnue : {mailbox}")
    return LocalMailbox.load(mailbox)


def _sse(event: dict) -> dict:
    return {"event": event["type"], "data": json.dumps(event, ensure_ascii=False)}


@app.get("/health")
def health() -> dict:
    s = get_settings()
    ok = s.anthropic_api_key is not None and s.typesafe_api_key is not None
    return {"status": "ok" if ok else "missing_keys",
            "models": {"agent": s.agent_model, "jev": s.typesafe_default_model}}


@app.get("/api/mailboxes")
def mailboxes() -> list[str]:
    return _mailboxes()


@app.get("/api/inbox")
def inbox(mailbox: str = "demo") -> list[dict]:
    return [{"id": m.id, "sender": m.sender, "subject": m.subject, "date": m.date}
            for m in _load(mailbox).list_mails()]


@app.get("/api/mails/{mail_id}")
def mail(mail_id: str, mailbox: str = "demo") -> dict:
    try:
        m = _load(mailbox).get(mail_id)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    return {"id": m.id, "sender": m.sender, "subject": m.subject, "date": m.date,
            "visible_text": m.canon.visible_text, "revealed_text": m.canon.revealed_text,
            "hidden": m.canon.hidden}


@app.post("/api/runs")
async def start_run(req: RunRequest) -> dict:
    _load(req.mailbox)
    log = RunLog()
    RUNS[log.run_id] = log
    task = asyncio.create_task(agent.run_agent(req.config, req.mailbox, req.instruction, log))
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
    return {"run_id": log.run_id}


async def live_events(events: list[dict]):
    sent = 0
    while True:
        while sent < len(events):
            event = events[sent]
            sent += 1
            yield _sse(event)
            if event["type"] == "run_finished":
                return
        await asyncio.sleep(0.1)


@app.get("/api/runs/{run_id}/events")
async def run_events(run_id: str) -> EventSourceResponse:
    if run_id not in RUNS:
        raise HTTPException(404, f"Run inconnu : {run_id}")
    return EventSourceResponse(live_events(RUNS[run_id].events))


# --- Replays : rejouer un run enregistré si le live échoue ---

def _replay_path(name: str):
    if not REPLAY_NAME.match(name):
        raise HTTPException(400, "Nom de replay : lettres minuscules, chiffres, - et _")
    return REPLAYS_DIR / f"{name}.jsonl"


@app.post("/api/runs/{run_id}/save")
def save_run(run_id: str, req: SaveRequest) -> dict:
    log = RUNS.get(run_id)
    if log is None or not log.events or log.events[-1]["type"] != "run_finished":
        raise HTTPException(409, "Le run n'existe pas ou n'est pas terminé")
    REPLAYS_DIR.mkdir(exist_ok=True)
    shutil.copyfile(log.path, _replay_path(req.name))
    return {"name": req.name}


@app.get("/api/replays")
def replays() -> list[dict]:
    items = []
    for path in sorted(REPLAYS_DIR.glob("*.jsonl")):
        events = RunLog.read(path)
        start = next((e for e in events if e["type"] == "run_started"), {})
        items.append({"name": path.stem, "config": start.get("config"),
                      "mailbox": start.get("mailbox"), "instruction": start.get("instruction"),
                      "duration": events[-1]["t"] if events else 0})
    return items


async def replay_events(events: list[dict], speed: float):
    previous = 0.0
    for event in events:
        await asyncio.sleep(max(0.0, event["t"] - previous) / speed)
        previous = event["t"]
        yield _sse(event)


@app.get("/api/replays/{name}/events")
async def replay(name: str, speed: float = 1.0) -> EventSourceResponse:
    path = _replay_path(name)
    if not path.exists():
        raise HTTPException(404, f"Replay inconnu : {name}")
    return EventSourceResponse(replay_events(RunLog.read(path), max(speed, 0.1)))
