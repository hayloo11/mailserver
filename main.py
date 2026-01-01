from imapclient import IMAPClient
from dotenv import load_dotenv
import os
import mailparser
import random
import string
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from Core.communication.mail.providers.mailcow import MailcowClient
import requests

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")

API_KEY = os.getenv("API_KEY")
MAIL_DOMAIN = os.getenv("MAIL_DOMAIN", "aupmail.xyz")

app = FastAPI(title="Private Temp Mail API")
mailcow = MailcowClient()

MAILCOW_URL = os.getenv("MAILCOW_URL", "https://mail.aupmail.xyz").rstrip("/")
MAILCOW_API_KEY = os.getenv("MAILCOW_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://temp.aupmail.xyz",
        "https://temp.aupmail.xyz",
        "http://api.aupmail.xyz",
        "https://api.aupmail.xyz"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def require_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def fetch_emails(limit: int = 50):
    emails = []
    with IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True) as server:
        server.login(IMAP_USER, IMAP_PASS)
        server.select_folder("INBOX")

        message_ids = server.search("ALL")
        message_ids = message_ids[-limit:]  # last N

        if not message_ids:
            return []

        resp = server.fetch(message_ids, ["RFC822"])

        for msgid in message_ids:
            raw = resp[msgid][b"RFC822"]
            mail = mailparser.parse_from_bytes(raw)

            emails.append({
                "id": int(msgid),
                "from": mail.from_[0][1] if mail.from_ else None,
                "to": mail.to[0][1] if mail.to else None,
                "subject": mail.subject,
                "date": str(mail.date),
                "text": mail.text_plain[0] if mail.text_plain else None,
                "html": mail.text_html[0] if mail.text_html else None,
            })

    return emails


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/new")
def new_inbox():
    name = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return {"name": name, "email": f"{name}@aupmain.xyz"}


@app.get("/inbox/{name}")
def inbox(name: str, limit: int = 50, x_api_key: str = Header(None)):
    require_key(x_api_key)
    target = f"{name}@{MAIL_DOMAIN}".lower()

    all_emails = fetch_emails(limit=limit)
    msgs = [m for m in all_emails if (m.get("to") or "").lower() == target]

    return {"inbox": target, "count": len(msgs), "messages": msgs}


@app.get("/emails")
def list_emails(limit: int = 10, x_api_key: str = Header(None)):
    require_key(x_api_key)
    return fetch_emails(limit=limit)

def require_api_key(x_api_key: str | None):
    if not x_api_key or x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/admin/delete")
def delete_mailboxes(emails: list[str], x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)

    url = f"{MAILCOW_URL}/api/v1/delete/mailbox"
    headers = {
        "X-API-Key": MAILCOW_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    r = requests.post(url, headers=headers, json=emails, timeout=20)
    return r.json()