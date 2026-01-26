import sqlite3
import os
from pathlib import Path
import threading
import json

_thread_local = threading.local()

def get_db_path() -> Path:
    """Returns the path to the SQLite database file."""
    db_dir = Path(os.path.expanduser("~/.local/share/chaos/logbooks"))
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "logbook.db"

def get_db_connection() -> sqlite3.Connection:
    """
    Gets a thread-local database connection.

    Enables WAL mode for better concurrency.
    """
    if not hasattr(_thread_local, 'connection'):
        db_path = get_db_path()
        # The timeout parameter is important for multi-threaded applications
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        _thread_local.connection = conn
    return _thread_local.connection

def close_db_connection():
    """Closes the thread-local database connection if it exists."""
    if hasattr(_thread_local, 'connection'):
        _thread_local.connection.close()
        del _thread_local.connection

def init_db():
    """
    Initializes the database and creates tables if they don't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table for runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        run_id_human TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL,
        status TEXT NOT NULL CHECK(status IN ('in_progress', 'success', 'failure')),
        summary_json TEXT,
        hailer_json TEXT
    )
    """)

    # Table for hosts within a run
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hosts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        name TEXT NOT NULL,
        summary_json TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE,
        UNIQUE (run_id, name)
    )
    """)

    # Table for operations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        host_id INTEGER NOT NULL,
        op_hash TEXT,
        name TEXT NOT NULL,
        changed INTEGER NOT NULL,
        success INTEGER NOT NULL,
        duration REAL NOT NULL,
        timestamp REAL NOT NULL,
        logs_json TEXT,
        diff TEXT,
        arguments_json TEXT,
        retry_stats_json TEXT,
        command_n_facts_in_order_json TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE,
        FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
    )
    """)

    # Table for resource snapshots
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        host_id INTEGER NOT NULL,
        stage TEXT,
        timestamp REAL NOT NULL,
        metrics_json TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE,
        FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
    )
    """)

    # Table for fact logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS command_n_facts_in_order (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        timestamp REAL NOT NULL,
        log_level TEXT,
        context TEXT,
        command TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE
    )
    """)

    conn.commit()

def create_run(run_id: str, run_id_human: str, start_time: float, hailer_info: dict) -> str:
    """Creates a new run entry in the database."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO runs (id, run_id_human, start_time, status, hailer_json) VALUES (?, ?, ?, ?, ?)",
        (run_id, run_id_human, start_time, 'in_progress', json.dumps(hailer_info))
    )
    conn.commit()
    return run_id

def get_or_create_host(run_id: str, host_name: str) -> int:
    """
    Retrieves the ID of a host if it exists for the current run,
    otherwise creates it and returns the new ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hosts WHERE run_id = ? AND name = ?", (run_id, host_name))
    row = cursor.fetchone()
    if row:
        return row['id']
    else:
        cursor.execute("INSERT INTO hosts (run_id, name) VALUES (?, ?)", (run_id, host_name))
        conn.commit()
        if not cursor.lastrowid:
            raise Exception("Failed to retrieve last inserted host ID.")

        return cursor.lastrowid

def insert_operation(run_id: str, host_id: int, op_hash: str, name: str, changed: bool, success: bool, duration: float, timestamp: float, logs: dict, diff: str, arguments: dict, retry_stats: dict, command_n_facts: list):
    """Inserts a new operation into the database."""
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO operations (run_id, host_id, op_hash, name, changed, success, duration, timestamp, logs_json, diff, arguments_json, retry_stats_json, command_n_facts_in_order_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, host_id, op_hash, name, int(changed), int(success), duration, timestamp, json.dumps(logs), diff, json.dumps(arguments), json.dumps(retry_stats), json.dumps(command_n_facts))
    )
    conn.commit()

def insert_snapshot(run_id: str, host_id: int, stage: str, timestamp: float, metrics: dict):
    """Inserts a resource snapshot into the database."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO resource_snapshots (run_id, host_id, stage, timestamp, metrics_json) VALUES (?, ?, ?, ?, ?)",
        (run_id, host_id, stage, timestamp, json.dumps(metrics))
    )
    conn.commit()

def insert_fact_log(run_id: str, timestamp: float, log_level: str, context: str, command: str):
    """Inserts a fact log entry."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO command_n_facts_in_order (run_id, timestamp, log_level, context, command) VALUES (?, ?, ?, ?, ?)",
        (run_id, timestamp, log_level, context, command)
    )
    conn.commit()

def update_run_status(run_id: str, status: str):
    """Updates the status of a run."""
    conn = get_db_connection()
    conn.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))
    conn.commit()

def end_run_update(run_id: str, end_time: float, status: str, summary: dict):
    """Updates a run at the end with final status, time, and summary."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE runs SET end_time = ?, status = ?, summary_json = ? WHERE id = ?",
        (end_time, status, json.dumps(summary), run_id)
    )
    conn.commit()

def get_facts_for_timespan(run_id: str, start_time: float, end_time: float) -> list[dict]:
    """Fetches fact logs within a given timespan for a run."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM command_n_facts_in_order WHERE run_id = ? AND timestamp >= ? AND timestamp < ?",
        (run_id, start_time, end_time)
    )
    return [dict(row) for row in cursor.fetchall()]

def get_run_summary_stats(run_id: str) -> dict:
    """Calculates summary statistics for a given run."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM operations WHERE run_id = ?", (run_id,))
    total_ops = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM operations WHERE run_id = ? AND changed = 1", (run_id,))
    changed_ops = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM operations WHERE run_id = ? AND success = 0", (run_id,))
    failed_ops = cursor.fetchone()[0]

    cursor.execute("SELECT sum(duration) FROM operations WHERE run_id = ?", (run_id,))
    total_duration_result = cursor.fetchone()[0]
    total_duration = round(total_duration_result, 4) if total_duration_result else 0.0

    return {
        'total_operations': total_ops,
        'changed_operations': changed_ops,
        'successful_operations': total_ops - failed_ops,
        'failed_operations': failed_ops,
        'total_duration': total_duration,
    }

# --- Functions to query data for reports ---

def get_run_data(run_id: str):
    """Fetches all data for a specific run."""
    conn = get_db_connection()

    run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not run:
        return None

    hosts_cursor = conn.execute("SELECT * FROM hosts WHERE run_id = ?", (run_id,))
    hosts = []
    for host_row in hosts_cursor:
        host_data = dict(host_row)
        ops_cursor = conn.execute("SELECT * FROM operations WHERE run_id = ? AND host_id = ? ORDER BY timestamp ASC", (run_id, host_row['id']))
        host_data['operations'] = [dict(op) for op in ops_cursor]
        hosts.append(host_data)

    snapshots_cursor = conn.execute("SELECT s.*, h.name as host_name FROM resource_snapshots s JOIN hosts h ON s.host_id = h.id WHERE s.run_id = ? ORDER BY s.timestamp ASC", (run_id,))
    snapshots = [dict(snap) for snap in snapshots_cursor]

    fact_logs_cursor = conn.execute("SELECT * FROM command_n_facts_in_order WHERE run_id = ? ORDER BY timestamp ASC", (run_id,))
    fact_logs = [dict(fact) for fact in fact_logs_cursor]

    return {
        "run": dict(run),
        "hosts": hosts,
        "snapshots": snapshots,
        "fact_logs": fact_logs
    }
