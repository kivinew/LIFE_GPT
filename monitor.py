#!/usr/bin/env python3
"""Monitor task queue status and report changes."""
import subprocess
import time
import sys
import os
from datetime import datetime

CHECK_INTERVAL = 600  # 10 minutes in seconds
LOG_FILE = "monitor.log"

def run_coordinator(args):
    """Run agent_coordinator.py with given args."""
    result = subprocess.run(
        ["python", "agent_coordinator.py"] + args,
        capture_output=True, text=True
    )
    return result.stdout.strip()

def get_pending_tasks():
    """Get list of pending/claimed tasks."""
    output = run_coordinator(["list"])
    lines = output.strip().split("\n")
    # Skip header lines
    tasks = []
    for line in lines[2:]:  # Skip header
        parts = line.split()
        if len(parts) >= 3:
            task_id = parts[0]
            status = parts[2]
            if status in ("pending", "claimed"):
                tasks.append((task_id, status))
    return tasks

def check_done_tasks():
    """Check for newly done tasks."""
    output = run_coordinator(["list"])
    lines = output.strip().split("\n")
    done_tasks = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) >= 3 and parts[2] == "done":
            done_tasks.append(parts[0])
    return done_tasks

def log_message(msg):
    """Write message to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def monitor():
    """Main monitoring loop."""
    log_message("Monitor started")
    
    known_done = set(check_done_tasks())
    
    while True:
        try:
            pending = get_pending_tasks()
            current_done = set(check_done_tasks())
            new_done = current_done - known_done
            
            if new_done:
                for task_id in new_done:
                    log_message(f"Task {task_id} completed! Running review...")
                    review = run_coordinator(["review", task_id])
                    log_message(f"Review {task_id}:\n{review[:500]}")
                    known_done.add(task_id)
            
            if not pending:
                log_message("All tasks completed!")
                break
            
            log_message(f"Pending: {len(pending)} tasks. Waiting {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("Monitor stopped by user")
            break
        except Exception as e:
            log_message(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single check mode
        pending = get_pending_tasks()
        done = check_done_tasks()
        print(f"Done: {len(done)} tasks")
        print(f"Pending/Claimed: {len(pending)} tasks")
        for task_id, status in pending:
            print(f"  {task_id}: {status}")
    else:
        monitor()
