"""Boîte mail locale : un fichier JSONL par boîte, brouillons en mémoire."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.canon import Canon, canonicalize

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mailboxes"


@dataclass
class Mail:
    id: str
    sender: str
    subject: str
    date: str
    body_text: str = ""
    body_html: str | None = None
    to: str = ""

    @property
    def canon(self) -> Canon:
        return canonicalize(self.body_text, self.body_html)


@dataclass
class Draft:
    to: str
    subject: str
    body: str
    in_reply_to: str | None = None


@dataclass
class LocalMailbox:
    name: str
    mails: dict[str, Mail]
    contacts: set[str] = field(default_factory=set)
    drafts: list[Draft] = field(default_factory=list)

    @classmethod
    def load(cls, name: str, directory: Path = FIXTURES) -> "LocalMailbox":
        raw = json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
        mails = {m["id"]: Mail(**m) for m in raw}
        contacts_file = directory / f"{name}.contacts.json"
        contacts = json.loads(contacts_file.read_text()) if contacts_file.exists() else []
        return cls(name, mails, {c.lower() for c in contacts})

    def is_contact(self, address: str) -> bool:
        return address.strip().lower() in self.contacts

    def provenance(self, address: str) -> str:
        """Ce que le guard sait du destinataire, établi par le code."""
        if self.is_contact(address):
            return "In the user's address book (known contact)."
        n = sum(m.sender.lower() == address.strip().lower() for m in self.mails.values())
        if n:
            return f"Not in the user's address book; {n} email(s) received from this address."
        return "Not in the user's address book; never wrote to this mailbox."

    def list_mails(self) -> list[Mail]:
        return list(self.mails.values())

    def get(self, mail_id: str) -> Mail:
        if mail_id not in self.mails:
            raise KeyError(f"Aucun mail avec l'identifiant {mail_id!r}")
        return self.mails[mail_id]

    def create_draft(self, to: str, subject: str, body: str, in_reply_to: str | None = None):
        self.drafts.append(Draft(to, subject, body, in_reply_to))
