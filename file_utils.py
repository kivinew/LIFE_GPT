# File utilities with locking for LIFE_GPT
# Prevents concurrent file access when multiple agents or processes touch project files
import os
import time
import json
import csv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def _lock_path(filepath):
    return filepath + ".lock"


def _ensure_parent_dir(filepath):
    """Ensure parent directory exists for lock file."""
    lock_dir = _lock_path(filepath)
    parent = os.path.dirname(lock_dir)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def lock_file(filepath):
    """Acquire exclusive lock on a file (blocks until available)."""
    _ensure_parent_dir(filepath)
    lock_dir = _lock_path(filepath)
    while True:
        try:
            os.mkdir(lock_dir)
            return
        except FileExistsError:
            time.sleep(0.05)


def try_lock_file(filepath, timeout=2.0):
    """Try to acquire lock, return True if acquired, False on timeout."""
    lock_dir = _lock_path(filepath)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.mkdir(lock_dir)
            return True
        except FileExistsError:
            time.sleep(0.05)
    return False


def unlock_file(filepath):
    """Release lock on a file."""
    lock_dir = _lock_path(filepath)
    try:
        os.rmdir(lock_dir)
    except (FileNotFoundError, OSError):
        pass


def locked_json_write(filepath, data):
    """Write JSON atomically with file locking."""
    lock_file(filepath)
    try:
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, filepath)
    finally:
        unlock_file(filepath)


def locked_json_read(filepath, default=None):
    """Read JSON with file locking. Returns default if file missing."""
    if not os.path.exists(filepath):
        return default if default is not None else {}
    lock_file(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        unlock_file(filepath)


def locked_fopen(filepath, mode="r", encoding="utf-8"):
    """Open a file with locking. Caller MUST call unlock_file when done."""
    lock_file(filepath)
    return open(filepath, mode, encoding=encoding)