from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, ToolMessage

from app.config import get_settings
from app.events import RunLog
from app.mailbox import LocalMailbox
from app.tools import Run, make_tools

SYSTEM_PROMPT = (
    "Tu es l'assistant mail de l'utilisateur. Tu traites sa boîte et tu rédiges des brouillons "
    "de réponse avec write_draft. Tu n'envoies jamais de mail et ne promets jamais d'envoyer."
)

# Le harness ne garde que nos tools : pas de filesystem, pas de shell, pas de subagent.
FILESYSTEM_TOOLS = frozenset(
    {"execute", "delete", "write_file", "edit_file", "ls", "read_file", "glob", "grep"}
)


def build_agent(run: Run):
    s = get_settings()
    model_id = s.agent_model.removeprefix("anthropic:")
    register_harness_profile(
        f"anthropic:{model_id}",
        HarnessProfile(excluded_tools=FILESYSTEM_TOOLS,
                       general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)),
    )
    model = ChatAnthropic(model=model_id, api_key=s.anthropic_api_key.get_secret_value(),
                          effort="low")
    return create_deep_agent(model=model, tools=make_tools(run), system_prompt=SYSTEM_PROMPT)


def _emit_message(log: RunLog, msg) -> None:
    if isinstance(msg, AIMessage):
        if msg.text.strip():
            log.emit("agent_message", text=msg.text)
        for call in msg.tool_calls:
            log.emit("tool_call", tool=call["name"], args=call["args"], call_id=call["id"])
    elif isinstance(msg, ToolMessage):
        log.emit("tool_result", tool=msg.name, call_id=msg.tool_call_id, text=str(msg.content)[:2000])


async def run_agent(config: str, mailbox_name: str, instruction: str, log: RunLog | None = None,
                    mailbox: LocalMailbox | None = None) -> Run:
    s = get_settings()
    log = log or RunLog()
    run = Run(config, mailbox or LocalMailbox.load(mailbox_name), instruction, log)
    log.emit("run_started", config=config, mailbox=mailbox_name, instruction=instruction,
             model=s.agent_model, jev=s.typesafe_default_model)
    try:
        agent = build_agent(run)
        async for update in agent.astream(
            {"messages": [{"role": "user", "content": instruction}]}, stream_mode="updates"
        ):
            for data in update.values():
                for msg in (data or {}).get("messages", []) if isinstance(data, dict) else []:
                    _emit_message(log, msg)
    except Exception as error:  # noqa: BLE001
        log.emit("error", message=f"{type(error).__name__}: {str(error)[:300]}")
    log.emit("run_finished", drafts=len(run.mailbox.drafts))
    return run
