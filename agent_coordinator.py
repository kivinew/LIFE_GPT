#!/usr/bin/env python3
"""
agent_coordinator.py — Task queue + locking for executor/controller agents.

USAGE:
  Controller (creates/re-prioritizes tasks):
    python agent_coordinator.py claim          # list tasks, claim next
    python agent_coordinator.py add "task"     # add new task
    python agent_coordinator.py log T17 "desc" # write progress log

  Executor (executes tasks):
    python agent_coordinator.py list           # list all tasks
    python agent_coordinator.py next           # get next available task
    python agent_coordinator.py claim T17      # claim specific task
    python agent_coordinator.py done T17       # mark complete
    python agent_coordinator.py review T17     # controller reviews

  Both:
    python agent_coordinator.py lock <file>    # acquire file lock
    python agent_coordinator.py unlock <file>  # release file lock
"""
import os, sys, json, time, datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_DIR = os.path.join(PROJECT_DIR, ".task_queue")
LOCK_DIR = os.path.join(PROJECT_DIR, ".locks")
LOG_DIR = os.path.join(PROJECT_DIR, ".agent_logs")

for d in (QUEUE_DIR, LOCK_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)


def _task_path(task_id):
    return os.path.join(QUEUE_DIR, f"{task_id}.json")


def _lock_path(name):
    return os.path.join(LOCK_DIR, name + ".lock")


def acquire_lock(name, timeout=5.0):
    """Directory-based mutex. Blocks until acquired or timeout."""
    path = _lock_path(name)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.mkdir(path)
            return True
        except FileExistsError:
            time.sleep(0.05)
    return False


def release_lock(name):
    path = _lock_path(name)
    try:
        os.rmdir(path)
    except (FileNotFoundError, OSError):
        pass


# ── Task operations ──────────────────────────────────────────────

def list_tasks():
    tasks = []
    for fn in sorted(os.listdir(QUEUE_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(QUEUE_DIR, fn)) as f:
                tasks.append(json.load(f))
    return sorted(tasks, key=lambda t: (t.get("priority", 99), t["id"]))


def claim_next(role="executor"):
    """Atomically claim the next available task. Uses queue lock to prevent race."""
    if not acquire_lock("queue", timeout=10.0):
        print("ERROR: could not acquire queue lock")
        return None
    try:
        tasks = list_tasks()
        for t in tasks:
            if t.get("status") == "pending":
                t["status"] = "claimed"
                t["assignee"] = role
                t["claimed_at"] = datetime.datetime.now().isoformat()
                with open(_task_path(t["id"]), "w") as f:
                    json.dump(t, f, indent=2)
                print(f"CLAIMED {t['id']} — {t['title']}")
                return t
        print("No pending tasks.")
        return None
    finally:
        release_lock("queue")


def mark_done(task_id, notes=""):
    if not acquire_lock("queue", timeout=10.0):
        print("ERROR: could not acquire queue lock")
        return
    try:
        path = _task_path(task_id)
        if not os.path.exists(path):
            print(f"ERROR: task {task_id} not found")
            return
        with open(path) as f:
            t = json.load(f)
        t["status"] = "done"
        t["done_at"] = datetime.datetime.now().isoformat()
        t["notes"] = notes
        with open(path, "w") as f:
            json.dump(t, f, indent=2)
        print(f"DONE {task_id} — {t['title']}")
    finally:
        release_lock("queue")


def add_task(title, priority="P1", details=""):
    """Controller: add a new task to the queue."""
    if not acquire_lock("queue", timeout=10.0):
        print("ERROR: could not acquire queue lock")
        return
    try:
        tasks = list_tasks()
        prefix = priority[0] if priority else "T"
        next_num = max([int(t["id"][1:]) for t in tasks if t["id"][1:].isdigit()], default=0) + 1
        task_id = f"{prefix}{next_num}"
        t = {
            "id": task_id,
            "title": title,
            "priority": priority,
            "details": details,
            "status": "pending",
            "assignee": None,
            "claimed_at": None,
            "done_at": None,
            "notes": "",
        }
        with open(_task_path(task_id), "w") as f:
            json.dump(t, f, indent=2)
        print(f"ADDED {task_id} [{priority}] — {title}")
    finally:
        release_lock("queue")


def write_log(task_id, message):
    """Append a timestamped log entry for a task."""
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, f"{task_id}.log")
    ts = datetime.datetime.now().isoformat()
    with open(path, "a") as f:
        f.write(f"[{ts}] {message}\n")


def claim_specific(task_id, role="executor"):
    """Claim a specific task by ID."""
    if not acquire_lock("queue", timeout=10.0):
        print("ERROR: could not acquire queue lock")
        return
    try:
        path = _task_path(task_id)
        if not os.path.exists(path):
            print(f"ERROR: task {task_id} not found")
            return
        with open(path) as f:
            t = json.load(f)
        if t["status"] != "pending":
            print(f"ERROR: task {task_id} is {t['status']}, not pending")
            return
        t["status"] = "claimed"
        t["assignee"] = role
        t["claimed_at"] = datetime.datetime.now().isoformat()
        with open(path, "w") as f:
            json.dump(t, f, indent=2)
        print(f"CLAIMED {task_id} — {t['title']}")
    finally:
        release_lock("queue")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "list":
        tasks = list_tasks()
        if not tasks:
            print("No tasks in queue.")
            return
        print(f"{'ID':<6} {'PRI':<6} {'STATUS':<10} {'ASSIGNEE':<12} TITLE")
        print("-" * 70)
        for t in tasks:
            print(f"{t['id']:<6} {t.get('priority',''):<6} {t['status']:<10} {str(t.get('assignee','')):<12} {t['title']}")

    elif cmd == "next":
        t = claim_next()
        if t:
            print(json.dumps(t, indent=2))

    elif cmd == "claim":
        if len(sys.argv) < 3:
            print("Usage: claim <task_id>")
            return
        claim_specific(sys.argv[2])

    elif cmd == "done":
        if len(sys.argv) < 3:
            print("Usage: done <task_id> [notes]")
            return
        notes = sys.argv[3] if len(sys.argv) > 3 else ""
        mark_done(sys.argv[2], notes)

    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: add \"title\" [priority] [details]")
            return
        priority = sys.argv[3] if len(sys.argv) > 3 else "P1"
        details = sys.argv[4] if len(sys.argv) > 4 else ""
        add_task(sys.argv[2], priority, details)

    elif cmd == "log":
        if len(sys.argv) < 4:
            print("Usage: log <task_id> \"message\"")
            return
        write_log(sys.argv[2], sys.argv[3])

    elif cmd == "lock":
        if len(sys.argv) < 3:
            print("Usage: lock <name>")
            return
        if acquire_lock(sys.argv[2]):
            print(f"Locked {sys.argv[2]}")
        else:
            print(f"Could not acquire lock {sys.argv[2]}")

    elif cmd == "unlock":
        if len(sys.argv) < 3:
            print("Usage: unlock <name>")
            return
        release_lock(sys.argv[2])
        print(f"Released lock {sys.argv[2]}")

    elif cmd == "review":
        if len(sys.argv) < 3:
            print("Usage: review <task_id>")
            return
        path = _task_path(sys.argv[2])
        if not os.path.exists(path):
            print(f"Task {sys.argv[2]} not found")
            return
        with open(path) as f:
            t = json.load(f)
        print(json.dumps(t, indent=2))
        log_path = os.path.join(LOG_DIR, f"{sys.argv[2]}.log")
        if os.path.exists(log_path):
            with open(log_path) as f:
                print("\n--- LOG ---")
                print(f.read())

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
