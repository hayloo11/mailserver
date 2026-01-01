// NOTE: This is client-side only. For private use it's fine.
// If you make this public, move auth server-side.
const API_KEY = "supersecretkey123";

let inboxName = null;

const elEmail = document.getElementById("email");
const elMsgs = document.getElementById("messages");
const toast = document.getElementById("toast");

const modal = document.getElementById("modal");
const modalClose = document.getElementById("modalClose");
const mFrom = document.getElementById("mFrom");
const mSubject = document.getElementById("mSubject");
const mBody = document.getElementById("mBody");

function showToast(text) {
  toast.textContent = text;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1200);
}

function openModal(msg) {
  mFrom.textContent = `From: ${msg.from || "—"} | To: ${msg.to || "—"}`;
  mSubject.textContent = msg.subject || "(no subject)";
  mBody.textContent = msg.text || stripHtml(msg.html || "") || "(empty)";
  modal.classList.add("show");
}

function stripHtml(html) {
  const div = document.createElement("div");
  div.innerHTML = html;
  return div.textContent || div.innerText || "";
}

async function apiGet(path) {
  const res = await fetch(path, {
    headers: { "X-API-Key": API_KEY }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function createInbox() {
  const data = await apiGet("/new");
  inboxName = data.name;
  elEmail.textContent = data.email;
  showToast("New inbox created");
  await loadInbox();
}

async function loadInbox() {
  if (!inboxName) return;

  const data = await apiGet(`/inbox/${inboxName}`);
  const messages = data.messages || [];

  elMsgs.innerHTML = "";

  if (messages.length === 0) {
    elMsgs.innerHTML = `<tr><td colspan="3" class="empty">Your inbox is empty</td></tr>`;
    return;
  }

  for (const msg of messages.reverse()) {
    const tr = document.createElement("tr");

    const from = document.createElement("td");
    from.textContent = msg.from || "—";

    const subject = document.createElement("td");
    subject.textContent = msg.subject || "(no subject)";

    const view = document.createElement("td");
    const btn = document.createElement("button");
    btn.className = "viewbtn";
    btn.textContent = "View";
    btn.onclick = () => openModal(msg);
    view.appendChild(btn);

    tr.appendChild(from);
    tr.appendChild(subject);
    tr.appendChild(view);

    elMsgs.appendChild(tr);
  }
}

document.getElementById("copy").onclick = async () => {
  await navigator.clipboard.writeText(elEmail.textContent);
  showToast("Copied!");
};

document.getElementById("refresh").onclick = loadInbox;
document.getElementById("change").onclick = createInbox;

document.getElementById("delete").onclick = () => {
  inboxName = null;
  elEmail.textContent = "Deleted";
  elMsgs.innerHTML = `<tr><td colspan="3" class="empty">Inbox deleted</td></tr>`;
  showToast("Deleted");
};

modalClose.onclick = () => modal.classList.remove("show");
modal.onclick = (e) => { if (e.target === modal) modal.classList.remove("show"); };

// Start
createInbox();

// Poll every 5 seconds
setInterval(loadInbox, 5000);