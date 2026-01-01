from imapclient import IMAPClient
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("IMAP_HOST")
PORT = int(os.getenv("IMAP_PORT", 993))
USER = os.getenv("IMAP_USER")
PASS = os.getenv("IMAP_PASS")

print("Connecting to IMAP...")

with IMAPClient(HOST, port=PORT, ssl=True) as server:
    server.login(USER, PASS)
    server.select_folder("INBOX")

    messages = server.search("ALL")
    print(f"Found {len(messages)} messages")

    if messages:
        print("Message IDs:", messages[:10])
