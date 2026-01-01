import os
import requests

class MailcowClient:
    def __init__(self):
        self.api_url = os.getenv("MAILCOW_API_URL")
        self.api_key = os.getenv("MAILCOW_API_KEY")

        if not self.api_url or not self.api_key:
            raise RuntimeError("MAILCOW_API_URL or MAILCOW_API_KEY missing in .env")

        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def delete_mailboxes(self, emails: list[str]) -> list[str]:
        if not emails:
            return []

        resp = requests.post(self.api_url, headers=self.headers, json=emails, timeout=15)

        if not resp.ok:
            raise RuntimeError(f"Mailcow delete failed: {resp.status_code} {resp.text}")

        deleted = []
        data = resp.json()
        for entry in data:
            if entry.get("type") == "success":
                # mailcow returns ["deleted", "email@domain"]
                msg = entry.get("msg", [])
                if isinstance(msg, list) and len(msg) > 1:
                    deleted.append(msg[1])
        return deleted