"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8010";

const EVENT_TYPES = [
  "run_started",
  "agent_message",
  "tool_call",
  "tool_result",
  "jev_verdict",
  "draft_created",
  "draft_blocked",
  "error",
  "run_finished",
];

type MailSummary = { id: string; sender: string; subject: string; date: string };
type MailDetail = MailSummary & { visible_text: string; revealed_text: string; hidden: string[] };
type RunEvent = { type: string; seq: number; t: number; [key: string]: any };
type Replay = { name: string; config: "A" | "B"; mailbox: string; instruction: string; duration: number };

const BAD = new Set(["quarantine", "block", "escalate", "error"]);

function tone(decision: string) {
  if (decision === "pass" || decision === "allow") return "bg-emerald-100 text-emerald-900 border-emerald-400";
  if (decision === "suspect") return "bg-amber-100 text-amber-900 border-amber-400";
  return "bg-red-100 text-red-900 border-red-500";
}

const DECISION_LABEL: Record<string, string> = {
  pass: "OK",
  suspect: "suspect",
  quarantine: "quarantaine",
  allow: "autorisé",
  escalate: "escalade (refus)",
  block: "bloqué",
  error: "Jev indisponible",
};

/** Surligne les secrets du scénario (code de porte, flag). */
function Secrets({ text }: { text: string }) {
  const parts = text.split(/(4729|INDABAX\{[^}]*\})/g);
  return (
    <>
      {parts.map((part, i) =>
        i % 2 ? (
          <mark key={i} className="bg-red-600 text-white font-bold px-1 rounded">
            {part}
          </mark>
        ) : (
          part
        ),
      )}
    </>
  );
}

/** Affiche le texte révélé : les passages cachés à un humain sont surlignés. */
function Revealed({ text }: { text: string }) {
  const parts = text.split(/\[(?:HIDDEN|HTML COMMENT)\] ([\s\S]*?) \[\/(?:HIDDEN|HTML COMMENT)\]/g);
  return (
    <>
      {parts.map((part, i) =>
        i % 2 ? (
          <span key={i} className="block my-2 bg-red-100 border-2 border-dashed border-red-500 text-red-900 p-2 rounded">
            👁 texte caché : {part}
          </span>
        ) : (
          part
        ),
      )}
    </>
  );
}

export default function Demo() {
  const [mailboxes, setMailboxes] = useState<string[]>(["demo"]);
  const [mailbox, setMailbox] = useState("demo");
  const [config, setConfig] = useState<"A" | "B">("A");
  const [instruction, setInstruction] = useState("Réponds aux nouveaux mails.");
  const [inbox, setInbox] = useState<MailSummary[]>([]);
  const [mail, setMail] = useState<MailDetail | null>(null);
  const [raw, setRaw] = useState(false);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [replays, setReplays] = useState<Replay[]>([]);
  const [runId, setRunId] = useState<string | null>(null); // dernier run live, pour l'enregistrer
  const [replaying, setReplaying] = useState<string | null>(null);
  const source = useRef<EventSource | null>(null);

  function loadReplays() {
    fetch(`${API}/api/replays`)
      .then((r) => r.json())
      .then(setReplays)
      .catch(() => {});
  }

  useEffect(loadReplays, []);

  useEffect(() => {
    fetch(`${API}/api/mailboxes`)
      .then((r) => r.json())
      .then(setMailboxes)
      .catch(() => setApiError(`Backend injoignable sur ${API}`));
  }, []);

  useEffect(() => {
    setMail(null);
    fetch(`${API}/api/inbox?mailbox=${mailbox}`)
      .then((r) => r.json())
      .then(setInbox)
      .catch(() => setApiError(`Backend injoignable sur ${API}`));
  }, [mailbox]);

  useEffect(() => () => source.current?.close(), []);

  async function openMail(id: string) {
    const r = await fetch(`${API}/api/mails/${id}?mailbox=${mailbox}`);
    setMail(await r.json());
    setRaw(false);
  }

  function listen(url: string) {
    source.current?.close();
    setEvents([]);
    setRunning(true);
    const es = new EventSource(url);
    source.current = es;
    for (const type of EVENT_TYPES) {
      es.addEventListener(type, (msg) => {
        const event = JSON.parse((msg as MessageEvent).data) as RunEvent;
        setEvents((prev) => (prev.some((e) => e.seq === event.seq) ? prev : [...prev, event]));
        if (type === "run_finished") {
          es.close();
          setRunning(false);
        }
      });
    }
    es.onerror = () => {
      es.close();
      setRunning(false);
    };
  }

  async function start() {
    setReplaying(null);
    setRunId(null);
    const r = await fetch(`${API}/api/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction, config, mailbox }),
    });
    const { run_id } = await r.json();
    setRunId(run_id);
    listen(`${API}/api/runs/${run_id}/events`);
  }

  function replay(name: string) {
    const item = replays.find((r) => r.name === name);
    if (!item) return;
    setConfig(item.config);
    setMailbox(item.mailbox);
    setInstruction(item.instruction);
    setRunId(null);
    setReplaying(name);
    listen(`${API}/api/replays/${name}/events`);
  }

  async function save() {
    const name = window.prompt("Nom du replay (minuscules, chiffres, - et _)", `demo-${config.toLowerCase()}`);
    if (!name || !runId) return;
    const r = await fetch(`${API}/api/runs/${runId}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!r.ok) window.alert((await r.json()).detail);
    loadReplays();
  }

  const verdicts = events.filter((e) => e.type === "jev_verdict");
  const jevByMail = new Map(verdicts.filter((v) => v.mail_id).map((v) => [v.mail_id, v]));
  const drafts = events.filter((e) => e.type === "draft_created" || e.type === "draft_blocked");
  const timeline = events.filter((e) => ["agent_message", "tool_call", "error"].includes(e.type));

  return (
    <main className="flex flex-col gap-4 p-4 text-lg h-screen">
      {/* Barre du haut */}
      <header className="flex flex-wrap items-center gap-4">
        <h1 className="text-2xl font-bold mr-4">Agent mail + Jev</h1>
        <div className="flex rounded-lg border-2 border-gray-800 overflow-hidden">
          {(["A", "B"] as const).map((c) => (
            <button
              key={c}
              onClick={() => setConfig(c)}
              className={`px-4 py-2 font-semibold ${config === c ? "bg-gray-900 text-white" : "bg-white"}`}
            >
              {c === "A" ? "A · Jev observe" : "B · Jev bloque"}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2">
          Boîte
          <select value={mailbox} onChange={(e) => setMailbox(e.target.value)} className="border-2 rounded px-2 py-1">
            {mailboxes.map((b) => (
              <option key={b}>{b}</option>
            ))}
          </select>
        </label>
        <select
          value=""
          onChange={(e) => replay(e.target.value)}
          disabled={running}
          className="border-2 rounded px-2 py-1"
        >
          <option value="">Replay…</option>
          {replays.map((r) => (
            <option key={r.name} value={r.name}>
              {r.name} ({r.config}, {r.duration.toFixed(0)} s)
            </option>
          ))}
        </select>
        {runId && !running && (
          <button onClick={save} className="border-2 border-gray-800 rounded px-3 py-1 font-semibold">
            Enregistrer comme démo
          </button>
        )}
        {replaying && <span className="text-sm bg-gray-200 rounded px-2 py-1">replay : {replaying}</span>}
        {apiError && <span className="text-red-700 font-semibold">{apiError}</span>}
      </header>

      <div className="grid grid-cols-[1fr_1.4fr_1fr] gap-4 flex-1 min-h-0">
        {/* Boîte */}
        <section className="border-2 rounded-xl p-3 overflow-auto">
          <h2 className="font-bold mb-2">Boîte</h2>
          <ul className="flex flex-col gap-2">
            {inbox.map((m) => {
              const v = jevByMail.get(m.id);
              return (
                <li key={m.id}>
                  <button
                    onClick={() => openMail(m.id)}
                    className={`w-full text-left border rounded-lg p-2 hover:bg-gray-50 ${mail?.id === m.id ? "border-gray-900 border-2" : ""}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold truncate">{m.subject}</span>
                      {v && (
                        <span className={`text-sm border rounded px-2 ${tone(v.decision)}`}>
                          Jev-I {v.scores.injection?.toFixed(2) ?? "?"}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 truncate">{m.sender}</div>
                  </button>
                </li>
              );
            })}
          </ul>
          {mail && (
            <article className="mt-4 border-t-2 pt-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold">{mail.subject}</h3>
                <button
                  onClick={() => setRaw(!raw)}
                  className={`text-sm border-2 rounded px-2 py-1 ${raw ? "bg-red-600 text-white border-red-600" : ""}`}
                >
                  {raw ? "Vue normale" : "Vue brute"}
                </button>
              </div>
              <div className="text-sm text-gray-600 mb-2">{mail.sender}</div>
              <p className="whitespace-pre-wrap">
                {raw ? <Revealed text={mail.revealed_text} /> : <Secrets text={mail.visible_text} />}
              </p>
            </article>
          )}
        </section>

        {/* Conversation */}
        <section className="border-2 rounded-xl p-3 flex flex-col min-h-0">
          <h2 className="font-bold mb-2">Conversation avec l&apos;agent</h2>
          <div className="flex gap-2 mb-3">
            <input
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              className="flex-1 border-2 rounded-lg px-3 py-2"
            />
            <button
              onClick={start}
              disabled={running}
              className="bg-gray-900 text-white font-semibold rounded-lg px-4 disabled:opacity-40"
            >
              {running ? "En cours…" : "Lancer"}
            </button>
          </div>
          <ol className="flex flex-col gap-2 overflow-auto">
            {timeline.map((e) => (
              <li key={e.seq} className="border rounded-lg p-2">
                <span className="text-sm text-gray-500 mr-2">{e.t.toFixed(1)} s</span>
                {e.type === "tool_call" && (
                  <span className="font-mono">
                    → <b>{e.tool}</b>
                    {e.tool === "read_mail" && `(${e.args.id})`}
                    {e.tool === "write_draft" && ` → ${e.args.to}`}
                  </span>
                )}
                {e.type === "agent_message" && <span className="whitespace-pre-wrap">{e.text}</span>}
                {e.type === "error" && <span className="text-red-700">{e.message}</span>}
              </li>
            ))}
          </ol>
        </section>

        {/* Panneau Jev */}
        <section className="border-2 rounded-xl p-3 overflow-auto">
          <h2 className="font-bold mb-2">Panneau Jev</h2>
          <ol className="flex flex-col gap-2">
            {verdicts.map((v) => (
              <li key={v.seq} className={`border-2 rounded-lg p-2 ${tone(v.decision)}`}>
                <div className="flex justify-between font-semibold">
                  <span>
                    {v.point} {v.mail_id ? `· mail ${v.mail_id}` : "· brouillon"}
                  </span>
                  <span>{v.latency_ms} ms</span>
                </div>
                <div className="font-mono text-base">
                  {Object.entries(v.scores as Record<string, number>)
                    .map(([k, p]) => `${k} = ${p.toFixed(2)}`)
                    .join("   ")}
                </div>
                <div>
                  {DECISION_LABEL[v.decision] ?? v.decision}
                  {!v.applied && BAD.has(v.decision) && <b> — Jev aurait bloqué</b>}
                </div>
                <div className="text-sm">{v.reason}</div>
              </li>
            ))}
          </ol>
        </section>
      </div>

      {/* Brouillons */}
      <section className="border-2 rounded-xl p-3 max-h-[30vh] overflow-auto">
        <h2 className="font-bold mb-2">Brouillons</h2>
        <div className="grid grid-cols-3 gap-3">
          {drafts.map((d) => (
            <div
              key={d.seq}
              className={`border-2 rounded-lg p-2 ${d.type === "draft_blocked" ? "border-red-600 bg-red-50" : d.would_block ? "border-amber-500" : "border-emerald-500"}`}
            >
              <div className="font-semibold">
                {d.type === "draft_blocked" ? "⛔ Bloqué" : "✉ Créé"} → {d.to}
              </div>
              {d.would_block && <div className="text-amber-800 font-semibold">Jev aurait bloqué</div>}
              <p className={`whitespace-pre-wrap text-base ${d.type === "draft_blocked" ? "line-through opacity-70" : ""}`}>
                <Secrets text={d.body} />
              </p>
              {d.type === "draft_blocked" && <div className="text-sm text-red-800">{d.reason}</div>}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
