"""Telemetry engine and pyinfra callbacks for tracking and recording operation execution metrics."""

import contextvars
import json
import logging
import os
import queue
import re
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING
from urllib import parse as urllib_parse

from pyinfra.api.host import Host
from pyinfra.api.operation import OperationMeta
from pyinfra.api.state import (
    BaseStateCallback,
    State,
    StateOperationHostData,
    StateOperationMeta,
)

from chaos.lib.plugDiscovery import get_plugins

from .limani.limani import Limani

if TYPE_CHECKING:
    from typing import TypedDict

    class OpPercentileReturn(TypedDict):
        count: int
        total_duration: float
        average_duration: float
        p50_duration: float
        p90_duration: float
        p95_duration: float
        p99_duration: float


op_hash_context: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "op_hash", default=None
)


class ChaosTelemetry(BaseStateCallback):
    """A telemetry system for tracking operation execution details in pyinfra-based chaos engineering experiments.

    This class captures detailed information about each operation and stores it in a local database via the Limani plugin.
    """

    _run_id: str | None = None
    _timers = {}
    _diff_log_buffer = {}
    _active_diffs = set()
    _db_writer_thread = None
    _poison_pill = object()
    _limani_plugin: Limani | None = None
    _secret_strings: set[str] = set()
    _needed_secret_keys: set[str] = set()

    @classmethod
    def _database_writer_worker(cls) -> None:
        """Worker thread to process database write operations asynchronously."""
        if not cls._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        cls._limani_plugin.connect()

        while True:
            try:
                if not cls._db_queue:
                    raise RuntimeError("DB queue is not initialized.")
                item = cls._db_queue.get()
                if item is cls._poison_pill:
                    cls._db_queue.task_done()
                    break

                func, args, kwargs = item
                func(*args, **kwargs)
                cls._db_queue.task_done()
            except Exception as e:
                print(f"Error in telemetry DB writer thread: {e}", flush=True)
        cls._limani_plugin.disconnect()

    @classmethod
    def start_run(cls) -> None:
        """Initializes the database, creates a new run entry, and starts the async DB writer.

        Notes:
            This should be called once at the beginning of a `chaos apply` execution.
        """
        if not cls._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        cls._limani_plugin.init_db()

        # Start the DB writer thread
        cls._db_queue = queue.Queue()
        cls._db_writer_thread = threading.Thread(
            target=cls._database_writer_worker, daemon=True
        )
        cls._db_writer_thread.start()

        run_id_human = f"chaos-{time.strftime('%Y/%m/%d-%H:%M:%S', time.gmtime())}"
        uggly_run_id = f"chaos-{int(time.time())}-{time.perf_counter_ns()}"

        hailer_info = {
            "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
            "boatswain": socket.gethostbyname(socket.gethostname()),
            "hostname": socket.gethostname(),
        }

        needed_secrets = cls._needed_secret_keys

        start_time = time.time()
        cls._run_id = cls._limani_plugin.create_run(
            uggly_run_id, run_id_human, start_time, hailer_info, needed_secrets
        )
        print(f"CHAOS_RUN_ID::{cls._run_id}", flush=True)

        cls._stream_chaos_event(
            {
                "type": "run_start",
                "run_id": run_id_human,
                "uggly_run_id": cls._run_id,
                "timestamp": start_time,
                "hailer": hailer_info,
                "secrets_required": list(needed_secrets),
            }
        )

    @classmethod
    def end_run(cls, status: str = "success") -> None:
        """Finalizes the run, updating its status and summary in the database.

        Args:
            status (str, optional): The final status of the run. Defaults to "success".

        Notes:
            This should be called once at the end of a `chaos apply` execution.
        """
        if not cls._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        if cls._run_id:
            # Wait for all pending writes to complete before finishing the run
            if cls._db_queue:
                cls._db_queue.join()

            conn = cls._limani_plugin.connect()
            try:
                final_status_row = conn.execute(
                    "SELECT status FROM runs WHERE id = ?", (cls._run_id,)
                ).fetchone()
                final_status = (
                    final_status_row["status"]
                    if final_status_row and final_status_row["status"] == "failure"
                    else status
                )

                summary = cls._limani_plugin.get_run_summary_stats(cls._run_id)
                summary["status"] = final_status

                end_time = time.time()
                # This final update should be synchronous to ensure it's done before exporting
                cls._limani_plugin.end_run_update(
                    cls._run_id, end_time, final_status, summary
                )
            finally:
                cls._limani_plugin.disconnect()

            cls._stream_chaos_event(
                {
                    "type": "run_end",
                    "run_id": cls._run_id,
                    "status": final_status,
                    "timestamp": end_time,
                    "summary": summary,
                }
            )

            # Stop the writer thread
            if cls._db_queue and cls._db_writer_thread:
                cls._db_queue.put(cls._poison_pill)
                cls._db_writer_thread.join()
                cls._db_writer_thread = None
                cls._db_queue = None

            print(f"CHAOS_RUN_ENDED::{cls._run_id}", flush=True)
            cls._run_id = None

    @staticmethod
    def _strip_ansi_codes(text: str) -> str:
        """Strips ANSI escape sequences from the provided string.

        Args:
            text (str): The text to be cleaned.

        Returns:
            str: The clean text.
        """
        ansi_escape = re.compile(r"\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]")
        return ansi_escape.sub("", text)

    @staticmethod
    def _sanitize_diff_text(text: str) -> str:
        """Redacts sensitive data and their common escaped variations from diff texts.

        Args:
            text (str): The raw diff text.

        Returns:
            str: Redacted diff text.
        """
        if not text:
            return text

        sensitive_strings = ChaosTelemetry._secret_strings

        valid_secrets_set = set()
        for s in sensitive_strings:
            s_str = str(s)
            if len(s_str) >= 4 and s_str.lower() not in (
                "true",
                "false",
                "null",
                "none",
            ):
                valid_secrets_set.add(s_str)
            for line in s_str.splitlines():
                clean_line = line.strip()
                if len(clean_line) >= 4 and clean_line.lower() not in (
                    "true",
                    "false",
                    "null",
                    "none",
                ):
                    valid_secrets_set.add(clean_line)

        valid_secrets = list(valid_secrets_set)
        valid_secrets.sort(key=len, reverse=True)

        for term in valid_secrets:
            escaped_term = re.escape(term)
            text = re.sub(escaped_term, "[REDACTED]", text, flags=re.IGNORECASE)

            url_encoded = urllib_parse.quote(term)
            if url_encoded != term:
                escaped_url = re.escape(url_encoded)
                text = re.sub(escaped_url, "[REDACTED_URL]", text, flags=re.IGNORECASE)

            json_escaped = json.dumps(term)[1:-1]
            if json_escaped != term:
                escaped_json = re.escape(json_escaped)
                text = re.sub(
                    escaped_json, "[REDACTED_JSON]", text, flags=re.IGNORECASE
                )

        for line in text.splitlines():
            if len(line.strip()) >= 4 and any(
                line in str(term)
                for term in sensitive_strings
                if len(str(term)) >= 4
                and str(term).lower() not in ("true", "false", "null", "none")
            ):
                text = text.replace(line, "[REDACTED_LINE]")

        return text

    @classmethod
    def record_setup_phase(cls, state: State, setup_duration: float) -> None:
        """Records the setup phase duration as a special operation in the database.

        Args:
            state (State): The pyinfra state object.
            setup_duration (float): The duration taken for the setup phase.
        """
        if not cls._run_id or not cls._db_queue:
            return

        if not cls._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        boatswain_hostname = socket.gethostname()
        host_id = cls._limani_plugin.get_or_create_host(
            cls._run_id, boatswain_hostname
        )  # This can remain sync

        ts = time.time()
        op_hash = f"setup-{time.perf_counter_ns()}"
        op_name = "chaos_setup"

        arguments = {"message": "Time spent connecting to hosts and preparing the run."}

        op_data = {
            "run_id": ChaosTelemetry._run_id,
            "host_id": host_id,
            "op_hash": op_hash,
            "name": op_name,
            "changed": False,
            "success": True,
            "duration": round(setup_duration, 4),
            "timestamp": ts,
            "logs": {},
            "diff": "",
            "arguments": arguments,
            "retry_stats": {},
            "command_n_facts": [],
        }
        cls._db_queue.put((cls._limani_plugin.insert_operation, [], op_data))

        streamed_event = {
            "type": "progress",
            "host": boatswain_hostname,
            "operation": op_name,
            "changed": False,
            "success": True,
            "duration": round(setup_duration, 4),
            "timestamp": ts,
            "logs": {},
            "diff": "",
            "operation_arguments": arguments,
            "retry_statistics": {},
            "command_n_fact_history": [],
        }
        cls._stream_chaos_event(streamed_event)

    @classmethod
    def record_snapshot(
        cls, host: Host, ram_data: dict, load_data: dict, stage: str = "checkpoint"
    ) -> None:
        """Records a snapshot of the host's resource usage into the database.

        Args:
            host (Host): The pyinfra target host object.
            ram_data (dict): The gathered dictionary containing RAM usage facts.
            load_data (dict): The gathered dictionary containing CPU Load facts.
            stage (str, optional): The identifier describing at what phase the snapshot was taken. Defaults to "checkpoint".
        """
        if not cls._run_id or not cls._db_queue:
            return

        if not cls._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        metrics = {
            "cpu_load_1min": load_data[0] if load_data else 0.0,
            "cpu_load_5min": load_data[1] if load_data else 0.0,
            "ram_percent": ram_data["percent"] if ram_data else 0.0,
            "ram_used_gb": round(ram_data["used_mb"] / 1024, 2) if ram_data else 0.0,
            "ram_total_gb": round(ram_data["total_mb"] / 1024, 2) if ram_data else 0.0,
        }

        ts = time.time()
        cls._stream_chaos_event(
            {
                "type": "health_check",
                "host": host.name,
                "stage": stage,
                "timestamp": ts,
                "metrics": metrics,
            }
        )

        host_id = cls._limani_plugin.get_or_create_host(
            cls._run_id, host.name
        )  # Sync is fine
        snapshot_data = {
            "run_id": cls._run_id,
            "host_id": host_id,
            "stage": stage,
            "timestamp": ts,
            "metrics": metrics,
        }
        cls._db_queue.put((cls._limani_plugin.insert_snapshot, [], snapshot_data))

    @staticmethod
    def _get_safe_logs(meta: OperationMeta) -> tuple[str, str]:
        """Safely retrieves stdout and stderr from the OperationMeta.

        Args:
            meta (OperationMeta): The pyinfra operation meta object.

        Returns:
            tuple[str, str]: Returns a tuple mapping stdout and stderr representations of the outputs.
        """
        if meta.is_complete():
            return ChaosTelemetry._sanitize_diff_text(
                meta.stdout
            ), ChaosTelemetry._sanitize_diff_text(meta.stderr)

        if hasattr(meta, "_combined_output") and meta._combined_output:
            return ChaosTelemetry._sanitize_diff_text(
                "\n".join(meta._combined_output.stdout_lines)
            ), ChaosTelemetry._sanitize_diff_text(
                "\n".join(meta._combined_output.stderr_lines)
            )

        return "", ""

    class PyinfraFactLogHandler(logging.Handler):
        """Gets command logs from pyinfra's logger and logs them to the database."""

        def emit(self, record):
            msg = record.getMessage()
            op_hash = op_hash_context.get()
            if not ChaosTelemetry._limani_plugin:
                raise RuntimeError("Limani plugin is not loaded.")

            # --- Diff handling (remains in-memory for the duration of exactly one op) ---
            if record.levelname == "INFO" and op_hash:
                is_diff_start = "Will modify" in msg
                is_part_of_active_diff = op_hash in ChaosTelemetry._active_diffs
                if is_diff_start:
                    ChaosTelemetry._active_diffs.add(op_hash)
                    is_part_of_active_diff = True

                if is_part_of_active_diff:
                    if op_hash not in ChaosTelemetry._diff_log_buffer:
                        ChaosTelemetry._diff_log_buffer[op_hash] = []

                    cleaned_msg = ChaosTelemetry._strip_ansi_codes(msg)

                    if "]" in cleaned_msg:
                        cleaned_msg = cleaned_msg.split("]", 1)[-1].strip()

                    cleaned_msg = ChaosTelemetry._sanitize_diff_text(cleaned_msg)

                    ChaosTelemetry._diff_log_buffer[op_hash].append(cleaned_msg)
                    if "Success" in msg or "No changes" in msg:
                        ChaosTelemetry._active_diffs.discard(op_hash)

                    return

            is_fact_gathering = "Getting fact:" in msg and record.levelname == "DEBUG"
            is_command_running = (
                "--> Running command" in msg and record.levelname == "DEBUG"
            )

            run_id = ChaosTelemetry._run_id
            if not run_id or not (is_fact_gathering or is_command_running):
                return

            context, command = None, None
            if is_fact_gathering:
                context = "fact_gathering"
                command = msg.split(":", 1)[-1].strip()

            elif is_command_running:
                try:
                    context_part, command_part = msg.split(":", 1)
                    context_text = context_part.split("-->")[1].strip()
                    context = context_text.replace(" ", "_").lower()
                    command = command_part.strip()
                except (ValueError, IndexError):
                    context = "running_command"
                    command = msg

            if command is not None:
                command = ChaosTelemetry._sanitize_diff_text(command)

            if context and command:
                ChaosTelemetry._stream_chaos_event(
                    {
                        "type": "fact",
                        "timestamp": record.created,
                        "log_level": record.levelname,
                        "context": context,
                        "command": command,
                    }
                )

                if ChaosTelemetry._db_queue:
                    log_data = {
                        "run_id": run_id,
                        "timestamp": record.created,
                        "log_level": record.levelname,
                        "context": context,
                        "command": command,
                    }
                    ChaosTelemetry._db_queue.put(
                        (ChaosTelemetry._limani_plugin.insert_fact_log, [], log_data)
                    )

    @staticmethod
    def operation_host_start(state: State, host: Host, op_hash: str) -> None:
        """Records the start time of an operation on a specific host.

        Args:
            state (State): The global state of the pyinfra run.
            host (Host): The host machine starting the operation.
            op_hash (str): The unique hash identifying the executing operation.
        """
        op_hash_context.set(op_hash)
        key = f"{host.name}:{op_hash}"
        ChaosTelemetry._timers[key] = time.time()

    @staticmethod
    def _parse_meta(meta: str) -> dict:
        """Parses operation metadata into a structured dictionary.

        Args:
            meta (str): String representation of the operation meta object.

        Returns:
            dict: The dictionary containing parsed attributes.
        """
        vars = meta.split("(")[1].split(")")[0]

        executed = vars.split("executed=")[1].split(",")[0]
        maybeChange = vars.split("maybeChange=")[1].split(",")[0]
        hash = vars.split("hash")[1].split(",")[0]

        clean_executed = ChaosTelemetry._clean_value(executed)
        clean_maybe = ChaosTelemetry._clean_value(maybeChange)

        return {"executed": clean_executed, "maybe_change": clean_maybe, "hash": hash}

    @staticmethod
    def _clean_value(value: str) -> str:
        """Cleans and evaluates string values safely.

        Args:
            value (str): Evaluated string data type.

        Returns:
            Any: The literal value interpretation or original string upon exception.
        """
        import ast

        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    @staticmethod
    def _sanitize_op_data(raw_data: dict[str, str]) -> dict[str, str]:
        """Cleanse op data to remove sensitive information before logging.

        Args:
            raw_data (dict): The dictionary representation of raw host execution properties.

        Returns:
            dict: The scrubbed and structured operations object dictionary.
        """

        clean_data = {}

        IGNORED_KEYS = ["state", "host", "command_generator"]

        SENSITIVE_TERMS = ["password", "secret", "token", "key", "auth", "sudo_pass"]

        for key, value in raw_data.items():
            if key in IGNORED_KEYS:
                continue

            elif key == "global_arguments":
                if isinstance(value, dict):
                    clean_data[key] = ChaosTelemetry._sanitize_op_data(value)

            elif key == "operation_meta":
                clean_data[key] = ChaosTelemetry._parse_meta(str(value))

            elif any(term in key.lower() for term in SENSITIVE_TERMS):
                clean_data[key] = "********"

            elif hasattr(value, "__call__"):
                clean_data[key] = "<function>"

            elif isinstance(value, str) and any(
                str(term).lower() in value
                for term in ChaosTelemetry._secret_strings
                if len(str(term)) >= 4
                and str(term).lower() not in ("true", "false", "null", "none")
            ):
                clean_data[key] = "********"

            else:
                clean_data[key] = ChaosTelemetry._clean_value(value)

        return clean_data

    @staticmethod
    def _stream_chaos_event(data: dict) -> None:
        """Helper to print event data as a structured JSON string.

        Args:
            data (dict): Dictionary context of the generated trace JSON.
        """
        print(f"CHAOS_EVENT::{json.dumps(data)}", flush=True)

    @staticmethod
    def operation_host_success(
        state: State, host: Host, op_hash, retry_count: int = 0
    ) -> None:
        """Handles the successful completion of an operation by writing to the DB.

        Args:
            state (State): Process state map.
            host (Host): Success targeted instance.
            op_hash (str): Operation map identity tracking the process context.
            retry_count (int, optional): Represents re-runs completed resolving it successfully. Defaults to 0.
        """
        end_time = time.time()

        if not ChaosTelemetry._run_id or not ChaosTelemetry._db_queue:
            return

        if not ChaosTelemetry._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        key = f"{host.name}:{op_hash}"
        start_time = ChaosTelemetry._timers.pop(key, None)
        duration = end_time - start_time if start_time else 0.0

        state_meta: StateOperationMeta = state.get_op_meta(op_hash)
        op_name = list(state_meta.names)[0] if state_meta.names else "unknown_operation"

        op_data: StateOperationHostData = state.get_op_data_for_host(host, op_hash)
        runtime_meta: OperationMeta = op_data.operation_meta
        stdout, stderr = ChaosTelemetry._get_safe_logs(runtime_meta)

        logs = {
            "stdout": stdout,
            "stderr": stderr,
        }

        retry_stats = {
            "retry_attempts": runtime_meta.retry_attempts,
            "max_retries": runtime_meta.max_retries,
            "retry_info": runtime_meta.get_retry_info(),
        }

        changed = runtime_meta.changed

        raw_data = vars(op_data)
        operation_arguments = ChaosTelemetry._sanitize_op_data(raw_data)

        diff_log = ChaosTelemetry._diff_log_buffer.pop(op_hash, [])
        diff_text = "\n".join(diff_log) if diff_log else ""

        command_n_facts = []
        if start_time:
            command_n_facts = ChaosTelemetry._limani_plugin.get_facts_for_timespan(
                ChaosTelemetry._run_id, start_time, end_time
            )

        streamed_event = {
            "type": "progress",
            "host": host.name,
            "operation": op_name,
            "changed": changed,
            "success": True,
            "duration": round(duration, 4),
            "timestamp": end_time,
            "logs": logs,
            "diff": diff_text,
            "operation_arguments": operation_arguments,
            "retry_statistics": retry_stats,
            "command_n_fact_history": command_n_facts,
        }

        ChaosTelemetry._stream_chaos_event(streamed_event)

        host_id = ChaosTelemetry._limani_plugin.get_or_create_host(
            ChaosTelemetry._run_id, host.name
        )

        db_op_data = {
            "run_id": ChaosTelemetry._run_id,
            "host_id": host_id,
            "op_hash": op_hash,
            "name": op_name,
            "changed": changed,
            "success": True,
            "duration": round(duration, 4),
            "timestamp": end_time,
            "logs": logs,
            "diff": diff_text,
            "arguments": operation_arguments,
            "retry_stats": retry_stats,
            "command_n_facts": command_n_facts,
        }
        ChaosTelemetry._db_queue.put(
            (ChaosTelemetry._limani_plugin.insert_operation, [], db_op_data)
        )

    @staticmethod
    def operation_host_error(
        state: State, host: Host, op_hash, retry_count: int = 0, max_retries: int = 0
    ) -> None:
        """Handles a failed operation by writing to the DB.

        Args:
            state (State): Pyinfra target operation's parent runtime config state reference.
            host (Host): Context Host identifier object marking what errored out.
            op_hash (str): The failing ops operation sequence lookup trace.
            retry_count (int, optional): Represents iteration amount tried. Defaults to 0.
            max_retries (int, optional): Hard limit defined on re-runs. Defaults to 0.
        """
        end_time = time.time()

        if not ChaosTelemetry._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        if not ChaosTelemetry._run_id or not ChaosTelemetry._db_queue:
            return

        key = f"{host.name}:{op_hash}"
        start_time = ChaosTelemetry._timers.pop(key, None)
        duration = end_time - start_time if start_time else 0.0

        static_meta = state.get_op_meta(op_hash)

        op_name = list(static_meta.names)[0] if static_meta.names else "Unknown Task"
        op_data = state.get_op_data_for_host(host, op_hash)
        raw_data = vars(op_data)
        operation_arguments = ChaosTelemetry._sanitize_op_data(raw_data)

        diff_log = ChaosTelemetry._diff_log_buffer.pop(op_hash, [])
        diff_text = "\n".join(diff_log) if diff_log else ""

        stdout, stderr = "", "Operation Failed."
        if hasattr(op_data, "operation_meta") and op_data.operation_meta:
            s_out, s_err = ChaosTelemetry._get_safe_logs(op_data.operation_meta)
            if s_out or s_err:
                stdout, stderr = s_out, s_err

        runtime_meta: OperationMeta = op_data.operation_meta

        logs = {"stdout": stdout, "stderr": stderr}
        retry_stats = {
            "retry_attempts": runtime_meta.retry_attempts,
            "max_retries": runtime_meta.max_retries,
            "retry_info": runtime_meta.get_retry_info(),
        }

        command_n_facts = []
        if start_time:
            command_n_facts = ChaosTelemetry._limani_plugin.get_facts_for_timespan(
                ChaosTelemetry._run_id, start_time, end_time
            )

        streamed_event = {
            "type": "progress",
            "host": host.name,
            "operation": op_name,
            "changed": False,
            "success": False,
            "duration": round(duration, 4),
            "timestamp": end_time,
            "logs": logs,
            "diff": diff_text,
            "operation_arguments": operation_arguments,
            "retry_statistics": retry_stats,
            "command_n_fact_history": command_n_facts,
        }

        ChaosTelemetry._stream_chaos_event(streamed_event)

        host_id = ChaosTelemetry._limani_plugin.get_or_create_host(
            ChaosTelemetry._run_id, host.name
        )

        db_op_data = {
            "run_id": ChaosTelemetry._run_id,
            "host_id": host_id,
            "op_hash": op_hash,
            "name": op_name,
            "changed": False,
            "success": False,
            "duration": round(duration, 4),
            "timestamp": end_time,
            "logs": logs,
            "diff": diff_text,
            "arguments": operation_arguments,
            "retry_stats": retry_stats,
            "command_n_facts": command_n_facts,
        }
        ChaosTelemetry._db_queue.put(
            (ChaosTelemetry._limani_plugin.insert_operation, [], db_op_data)
        )
        ChaosTelemetry._db_queue.put(
            (
                ChaosTelemetry._limani_plugin.start_update_run,
                [ChaosTelemetry._run_id, "failure"],
                {},
            )
        )

    @staticmethod
    def percentile(data: list, percentile_val: float) -> float:
        """Calculates the given percentile from a list of numbers.

        Args:
            data (list): The list of numerical values to extract percentiles against.
            percentile_val (float): Percentile targeted between (0 - 100).

        Returns:
            float: Returns the identified threshold float.
        """
        if not data:
            return 0.0
        size = len(data)
        sorted_data = sorted(data)
        k = (size - 1) * (percentile_val / 100)
        f = int(k)
        c = k - f
        if f + 1 < size:
            return round(
                sorted_data[f] + (c * (sorted_data[f + 1] - sorted_data[f])), 4
            )
        else:
            return round(sorted_data[f], 4)

    @staticmethod
    def add_operation_percentiles(
        op_durations: dict[str, list[float]],
    ) -> dict[str, OpPercentileReturn]:
        """Calculates and adds operation duration percentiles to the report data.

        Args:
            op_durations (dict): A dictionary linking operations to execution logs' time spans arrays.

        Returns:
            dict: The dictionary wrapping summary map data representations and percentiles context.
        """
        op_summary = {}

        for name, durations in op_durations.items():
            count = len(durations)
            total_duration = round(sum(durations), 4)

            op_summary[name] = {
                "count": count,
                "total_duration": total_duration,
                "average_duration": round(total_duration / count, 4)
                if count > 0
                else 0.0,
                "p50_duration": ChaosTelemetry.percentile(durations, 50),
                "p90_duration": ChaosTelemetry.percentile(durations, 90),
                "p95_duration": ChaosTelemetry.percentile(durations, 95),
                "p99_duration": ChaosTelemetry.percentile(durations, 99),
            }

        return op_summary

    @classmethod
    def export_report(cls, filepath: str = "chaos_logbook.json") -> None:
        """Fetches run data and generates a structured JSON report by streaming.

        Args:
            filepath (str, optional): The target local export file. Defaults to "chaos_logbook.json".

        Notes:
            Streaming avoids loading the entire dataset into memory.
            Yeah, i know it writes directly to a file first, but it's still better than loading everything into memory before writing.
        """
        import shutil

        if not cls._run_id:
            print("No active run to export.")
            return

        if not cls._limani_plugin:
            raise RuntimeError("Limani plugin is not loaded.")

        # Ensure all pending writes are finished before exporting
        if cls._db_queue:
            cls._db_queue.join()

        db_data = cls._limani_plugin.get_run_data(cls._run_id)
        if not db_data:
            print(f"Could not find data for run_id: {cls._run_id}")
            return

        run_info = db_data["run"]

        try:
            with open(filepath, "w") as f:
                f.write("{\n")
                # Write top-level info
                f.write('    "api_version": "v1",\n')
                f.write(f'    "run_id": {json.dumps(run_info["run_id_human"])},\n')
                f.write(f'    "uggly_run_id": {json.dumps(run_info["id"])},\n')
                f.write(
                    f'    "hailer": {json.dumps(json.loads(run_info["hailer_json"]) if run_info["hailer_json"] else {})},\n'
                )
                f.write(
                    f'    "secrets_required": {json.dumps(list(cls._needed_secret_keys))},\n'
                )

                f.write('    "hosts": {\n')
                op_durations_for_percentiles = {}
                host_entries = []

                for host_data in db_data["hosts"]:
                    host_name = host_data["name"]
                    host_history = []
                    host_total_ops = len(host_data["operations"])
                    host_changed_ops = 0
                    host_failed_ops = 0
                    host_duration = 0.0

                    for op_row in host_data["operations"]:
                        op_details = {
                            "operation": op_row["name"],
                            "changed": bool(op_row["changed"]),
                            "success": bool(op_row["success"]),
                            "duration": op_row["duration"],
                            "stdout": json.loads(op_row["logs_json"]).get("stdout", "")
                            if op_row["logs_json"]
                            else "",
                            "stderr": json.loads(op_row["logs_json"]).get("stderr", "")
                            if op_row["logs_json"]
                            else "",
                            "diff": op_row["diff"],
                            "operation_arguments": json.loads(op_row["arguments_json"])
                            if op_row["arguments_json"]
                            else {},
                            "retry_statistics": json.loads(op_row["retry_stats_json"])
                            if op_row["retry_stats_json"]
                            else {},
                        }
                        host_history.append(op_details)

                        host_duration += op_row["duration"]
                        if bool(op_row["changed"]):
                            host_changed_ops += 1
                        if not bool(op_row["success"]):
                            host_failed_ops += 1

                        op_name = op_row["name"]
                        if op_name not in op_durations_for_percentiles:
                            op_durations_for_percentiles[op_name] = []
                        op_durations_for_percentiles[op_name].append(op_row["duration"])

                    host_summary = {
                        "total_operations": host_total_ops,
                        "changed_operations": host_changed_ops,
                        "successful_operations": host_total_ops - host_failed_ops,
                        "failed_operations": host_failed_ops,
                        "duration": round(host_duration, 4),
                        "history": host_history,
                    }
                    host_entries.append(
                        f"        {json.dumps(host_name)}: {json.dumps(host_summary, indent=4)}"
                    )

                f.write(",\n".join(host_entries))
                f.write("\n    },\n")

                summary_stats = cls._limani_plugin.get_run_summary_stats(cls._run_id)
                summary_stats["status"] = run_info["status"]
                f.write(f'    "summary": {json.dumps(summary_stats, indent=4)},\n')

                resource_history = [
                    {
                        "type": "health_check",
                        "host": snap_row["host_name"],
                        "stage": snap_row["stage"],
                        "timestamp": snap_row["timestamp"],
                        "metrics": json.loads(snap_row["metrics_json"])
                        if snap_row["metrics_json"]
                        else {},
                    }
                    for snap_row in db_data["snapshots"]
                ]
                f.write(
                    f'    "resource_history": {json.dumps(resource_history, indent=4)},\n'
                )

                fact_history = [
                    dict(log)
                    for log in db_data["fact_logs"]
                    if log["context"] == "fact_gathering"
                ]
                f.write(f'    "fact_history": {json.dumps(fact_history, indent=4)},\n')

                streamed_history = []
                for host_data in db_data["hosts"]:
                    for op in host_data["operations"]:
                        streamed_event = {
                            "type": "progress",
                            "host": host_data["name"],
                            "operation": op["name"],
                            "changed": bool(op["changed"]),
                            "success": bool(op["success"]),
                            "duration": op["duration"],
                            "logs": json.loads(op["logs_json"])
                            if op["logs_json"]
                            else {},
                            "diff": op["diff"],
                            "operation_arguments": json.loads(op["arguments_json"])
                            if op["arguments_json"]
                            else {},
                            "retry_statistics": json.loads(op["retry_stats_json"])
                            if op["retry_stats_json"]
                            else {},
                            "command_n_fact_history": json.loads(
                                op["command_n_facts_in_order_json"]
                            )
                            if op["command_n_facts_in_order_json"]
                            else [],
                        }
                        streamed_history.append(streamed_event)

                streamed_history.sort(key=lambda x: x.get("timestamp", 0))
                f.write(
                    f'    "streamed_history": {json.dumps(streamed_history, indent=4)},\n'
                )

                op_summary = cls.add_operation_percentiles(op_durations_for_percentiles)
                f.write(
                    f'    "operation_summary": {json.dumps(op_summary, indent=4)}\n'
                )

                f.write("}\n")

            try:
                print("CHAOS_LOGBOOK::", end="", flush=True)

                subprocess.run(["jq", "-c", ".", filepath], check=True)

            except FileNotFoundError:
                import sys

                print("{}", flush=True)
                print(
                    "Warning: 'jq' not found. Please install 'jq' to format the logbook output.",
                    file=sys.stderr,
                )
            except Exception as e:
                import sys

                print("{}", flush=True)
                print(f"Error executing jq: {e}", file=sys.stderr)

            logbook_dir = Path(
                os.getenv(
                    "CHAOS_LOGBOOK_DIR",
                    Path.home() / ".local" / "share" / "chaos" / "logbooks",
                )
            )
            amount = len(list(logbook_dir.glob("chaos_logbook_*.json")))
            shutil.copy(
                filepath,
                logbook_dir / f"chaos_logbook_run{amount + 1}_{int(time.time())}.json",
            )

        except Exception as e:
            print(f"Error writing final report: {e}")

    @classmethod
    def load_limani_plugin(cls, limani_name: str, global_config: dict) -> None:
        """Loads a given limani plugin by its name.

        Args:
            limani_name (str): The name identifier for the specific limani data store extension.
            global_config (dict): The global configuration dictionary.

        Raises:
            ImportError: Upon plugin loading error attributes failing.
            ValueError: If specific limani definition name is unassigned in known namespace.
        """
        from importlib.metadata import EntryPoint

        limanis = get_plugins()[6]
        for name, value in limanis.items():
            if name == limani_name:
                ep = EntryPoint(name=name, value=value, group="chaos.limani")
                try:
                    Plugin = ep.load()
                    cls._limani_plugin = Plugin(global_config)
                    return
                except (ImportError, AttributeError, ValueError) as e:
                    raise ImportError(
                        f"Could not load Limani plugin '{limani_name}': {e}"
                    )

        raise ValueError(f"Limani plugin '{limani_name}' not found.")
