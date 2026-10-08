"""Simple Ticketing Logic. Runs in the browser via Pyodide (Python compiled to WebAssembly).
index.html loads this file and calls the functions below... 
every function returns a JSON string.

Data is kept in the browser's localStorage.
"""
import json
from datetime import datetime, timezone

STATUSES = ["open", "in_progress", "resolved", "closed"]
PRIORITIES = ["low", "medium", "high", "urgent"]
KEY = "ticketing-system-v1"

try:
    from js import localStorage  
except ImportError:
    localStorage = None

_memory = None  


def _load():
    if localStorage is not None:
        try:
            raw = localStorage.getItem(KEY)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _memory or {"nextId": 1, "tickets": []}


def _save(data):
    global _memory
    _memory = data
    if localStorage is not None:
        try:
            localStorage.setItem(KEY, json.dumps(data))
        except Exception:
            pass


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _find(data, tid):
    return next((t for t in data["tickets"] if t["id"] == int(tid)), None)


def _err(msg):
    return json.dumps({"error": msg})


def list_tickets(status=""):
    tickets = [t for t in _load()["tickets"] if not status or t["status"] == status]
    tickets.sort(key=lambda t: t["updated_at"], reverse=True)
    return json.dumps(tickets)


def get_ticket(tid):
    t = _find(_load(), tid)
    return json.dumps(t) if t else _err("Ticket not found.")


def create_ticket(title, description, requester, priority):
    title, requester = title.strip(), requester.strip()
    if not title or not requester:
        return _err("Title and your name are required.")
    data = _load()
    now = _now()
    ticket = {
        "id": data["nextId"],
        "title": title,
        "description": description.strip(),
        "requester": requester,
        "status": "open",
        "priority": priority if priority in PRIORITIES else "medium",
        "created_at": now,
        "updated_at": now,
        "comments": [],
    }
    data["nextId"] += 1
    data["tickets"].append(ticket)
    _save(data)
    return json.dumps(ticket)


def update_ticket(tid, status="", priority=""):
    data = _load()
    t = _find(data, tid)
    if not t:
        return _err("Ticket not found.")
    if status in STATUSES:
        t["status"] = status
    if priority in PRIORITIES:
        t["priority"] = priority
    t["updated_at"] = _now()
    _save(data)
    return json.dumps(t)


def add_comment(tid, author, body):
    author, body = author.strip(), body.strip()
    if not author or not body:
        return _err("Name and comment are required.")
    data = _load()
    t = _find(data, tid)
    if not t:
        return _err("Ticket not found.")
    now = _now()
    t["comments"].append({"author": author, "body": body, "created_at": now})
    t["updated_at"] = now
    _save(data)
    return json.dumps(t)


def delete_ticket(tid):
    data = _load()
    data["tickets"] = [t for t in data["tickets"] if t["id"] != int(tid)]
    _save(data)
    return json.dumps({"ok": True})


def export_data():
    return json.dumps(_load(), indent=2)


def import_data(text):
    try:
        data = json.loads(text)
        if not isinstance(data["tickets"], list) or not isinstance(data["nextId"], int):
            raise ValueError
    except Exception:
        return _err("That file is not a valid ticket backup.")
    _save(data)
    return json.dumps({"ok": True})