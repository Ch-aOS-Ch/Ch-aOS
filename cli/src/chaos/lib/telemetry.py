import json
import time
import logging
import contextvars
import re
import os
from pathlib import Path
import tempfile
import threading

from pyinfra.api.operation import OperationMeta
from pyinfra.api.state import State, BaseStateCallback, StateOperationHostData, StateOperationMeta
from pyinfra.api.host import Host

op_hash_context: contextvars.ContextVar[str | None] = contextvars.ContextVar('op_hash', default=None)

class ChaosTelemetry(BaseStateCallback):
    """
    A telemetry system for tracking operation execution details in pyinfra-based chaos engineering experiments.
    This class captures detailed information about each operation performed on hosts, including
    whether the operation resulted in changes, succeeded, or failed. It also records execution duration
    and logs (stdout and stderr) associated with each operation.

    Key Features:
    - Operation Timing: Measures the duration of each operation on a per-host-basis.

    - Event Streaming: Streams real-time progress events to standard output, which can be captured by
        external systems for monitoring or logging purposes.

    - Statistics Tracking: Maintains comprehensive statistics at both the summary level and per-host level,
        including total operations, changed operations, successful operations, failed operations, and total duration.

    - Detailed Logging: Captures and stores stdout and stderr logs for each operation, along with
        retry information if applicable.

    - Report Generation: Provides functionality to export a detailed report of all operations
        Executed during the chaos experiment to a JSON file.
    """
    _lock = threading.Lock()
    _thread_local = threading.local()
    _temp_log_dir = None
    _temp_log_files = set()

    _process = None
    _timers = {}
    _fact_log_buffer = {}
    _diff_log_buffer = {}
    _active_diffs = set()
    _report_data = {
        'api_version': 'v1',
        'run_id': f"chaos-{time.strftime('%Y/%m/%d-%H:%M:%S', time.gmtime())}",
        'uggly_run_id': f"chaos-{int(time.time())}-{time.perf_counter_ns()}",
        'hailer': {},
        'hosts': {},
        'summary': {
            'total_operations': 0,
            'changed_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'status': 'success',
            'total_duration': 0.0,
        },
        'operation_summary': {},
    }

    @classmethod
    def _log_event_to_file_and_stdout(cls, event_payload: dict):
        """
        Aggregates the logic for printing an event to stdout and saving it to the thread-local temporary file.
        """
        json_payload = json.dumps(event_payload)
        print(f"CHAOS_EVENT::{json_payload}", flush=True)

        log_file = cls._get_thread_local_log_file()
        log_file.write(json_payload + '\n')

    @classmethod
    def _get_thread_local_log_file(cls):
        """
        Gets or creates a thread-local log file handle.
        This ensures that each thread writes to its own temporary file, avoiding race conditions.
        """
        if not hasattr(cls._thread_local, 'log_file_handle'):
            with cls._lock:
                if cls._temp_log_dir is None:
                    cls._temp_log_dir = tempfile.mkdtemp(prefix="chaos_run_")

                thread_id = threading.get_ident()
                temp_file_path = os.path.join(cls._temp_log_dir, f"thread_{thread_id}.jsonl")

                handle = open(temp_file_path, 'w')
                cls._thread_local.log_file_handle = handle
                cls._temp_log_files.add(temp_file_path)

        return cls._thread_local.log_file_handle

    @staticmethod
    def _strip_ansi_codes(text: str) -> str:
        # Regex to remove ANSI escape codes
        ansi_escape = re.compile(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')
        return ansi_escape.sub('', text)

    @staticmethod
    def _sanitize_diff_text(text):

        sensitive_terms = ['password', 'secret', 'token', 'key', 'auth', 'sudo_pass']

        for term in sensitive_terms:
            if term in text.lower():
                lines = text.split('\n')
                sanitized_lines = [
                    f"[SENSITIVE DATA FILTERED]" if term in line.lower() else line
                    for line in lines
                ]
                text = '\n'.join(sanitized_lines)

        return text

    @staticmethod
    def record_setup_phase(state: State, setup_duration: float):
        """
        Records the setup phase duration in the telemetry report.
        """
        setup_event = {
            "type": "setup_phase",
            "stage": "connection_and_facts",
            "timestamp": time.time(),
            "duration": round(setup_duration, 4),
            "success": True
        }

        # Use the new centralized logging method
        ChaosTelemetry._log_event_to_file_and_stdout(setup_event)

        for host in state.inventory.iter_activated_hosts():
            if host.name not in ChaosTelemetry._report_data['hosts']:
                ChaosTelemetry._report_data['hosts'][host.name] = {
                    'total_operations': 0,
                    'changed_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'duration': 0.0
                }


    @staticmethod
    def record_snapshot(host: Host, ram_data: dict, load_data: dict, stage: str = "checkpoint"):
        """
        Records a snapshot of the host's resource usage (RAM and CPU load) at a specific
        """
        snapshot = {
            "type": "health_check",
            "host": host.name,
            "stage": stage,
            "timestamp": time.time(),
            "metrics": {
                "cpu_load_1min": load_data[0] if load_data else 0.0,
                "cpu_load_5min": load_data[1] if load_data else 0.0,
                "ram_percent": ram_data['percent'] if ram_data else 0.0,
                "ram_used_gb": round(ram_data['used_mb'] / 1024, 2) if ram_data else 0.0,
                "ram_total_gb": round(ram_data['total_mb'] / 1024, 2) if ram_data else 0.0,
            }
        }

        ChaosTelemetry._log_event_to_file_and_stdout(snapshot)
        return snapshot

    @staticmethod
    def _get_safe_logs(meta: OperationMeta):
        """
        Since we use run_ops to run operations, the stdout/stderr may not be directly available.
        This method safely retrieves stdout and stderr from the OperationMeta.
        """
        if meta.is_complete():
            return meta.stdout, meta.stderr

        if hasattr(meta, '_combined_output') and meta._combined_output:
            return "\n".join(meta._combined_output.stdout_lines), "\n".join(meta._combined_output.stderr_lines)

        return "", ""

    class PyinfraFactLogHandler(logging.Handler):
        """
        gets command logs from pyinfra's logger
        """

        def emit(self, record):
            msg = record.getMessage()
            op_hash = op_hash_context.get()

            if record.levelname == 'INFO' and op_hash:
                is_diff_start = 'Will modify' in msg
                is_part_of_active_diff = op_hash in ChaosTelemetry._active_diffs

                if is_diff_start:
                    ChaosTelemetry._active_diffs.add(op_hash)
                    is_part_of_active_diff = True

                if is_part_of_active_diff:
                    if op_hash not in ChaosTelemetry._diff_log_buffer:
                        ChaosTelemetry._diff_log_buffer[op_hash] = []

                    cleaned_msg = ChaosTelemetry._strip_ansi_codes(msg)

                    if ']' in cleaned_msg:
                        cleaned_msg = cleaned_msg.split(']', 1)[-1].strip()

                    cleaned_msg = ChaosTelemetry._sanitize_diff_text(cleaned_msg)

                    ChaosTelemetry._diff_log_buffer[op_hash].append(cleaned_msg)

                    if 'Success' in msg or 'No changes' in msg:
                        ChaosTelemetry._active_diffs.discard(op_hash)
                    return

            is_fact_gathering = "Getting fact:" in msg and record.levelname == 'DEBUG'
            is_command_running = "--> Running command" in msg and record.levelname == 'DEBUG'

            if not op_hash and not is_fact_gathering and not is_command_running:
                return

            key = op_hash

            if not op_hash and is_fact_gathering:
                parts = msg.split(":")
                command = parts[1].strip().replace(" ", "_").lower()
                key = f"__facts_for_{command}"

            if not key:
                return

            context = None
            command = None

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

            if context and command:
                if key not in ChaosTelemetry._fact_log_buffer:
                    ChaosTelemetry._fact_log_buffer[key] = []

                log_entry = {
                    "timestamp": record.created,
                    "log_level": record.levelname,
                    "context": context,
                    "command": command,
                }

                if not op_hash:
                    fact_event = {
                        "type": "fact_log_event",
                        "timestamp": record.created,
                        "log_level": record.levelname,
                        "context": context,
                        "command": command,
                    }
                    ChaosTelemetry._log_event_to_file_and_stdout(fact_event)

                ChaosTelemetry._fact_log_buffer[key].append(log_entry)

    @staticmethod
    def _stream_event(host: Host, op_name, changed: bool, failed: bool, retry_count: int = 0, duration: float = 0.0, logs: dict = {}, op_hash: str = "", diff_log: str = "", operation_arguments: dict = {}, retry_statistics: dict = {}):
        """
        Streams a progress event to standard output in JSON format.

        This is useful for real-time monitoring of operation execution.
        Good for integrating with external logging or monitoring systems.

        Optionally, includes an way to save the event history, not currently used because of
        hosts history tracking.
        """

        operation_fact_logs = ChaosTelemetry._fact_log_buffer.pop(op_hash, [])

        payload = {
            "type": "progress",
            "host": host.name,
            "operation": op_name,
            "changed": changed,
            "success": not failed,
            'retry_count': retry_count,
            'duration': duration,
            # 'facts_collected': facts,
            # 'operation_commands': commands,
            'command_n_facts_in_order': operation_fact_logs,
            'logs': logs,
            'diff': diff_log,
            'operation_arguments': operation_arguments or {},
            'retry_statistics': retry_statistics or {},
        }

        ChaosTelemetry._log_event_to_file_and_stdout(payload)

    @staticmethod
    def _update_statistics(host: Host, changed: bool, failed: bool, duration: float, op_details: dict):
        """
        Updates the telemetry statistics with the results of an operation executed on a host.
        This method is now thread-safe.
        """
        with ChaosTelemetry._lock:
            stats = ChaosTelemetry._report_data
            if host.name not in stats['hosts']:
                stats['hosts'][host.name] = {
                    'total_operations': 0,
                    'changed_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'duration': 0.0,
                }

            stats['summary']['total_operations'] += 1
            stats['summary']['total_duration'] += duration
            if changed:
                stats['summary']['changed_operations'] += 1
            if failed:
                stats['summary']['failed_operations'] += 1
                stats['summary']['status'] = 'failure'

            host_stats = stats['hosts'][host.name]
            host_stats['total_operations'] += 1
            host_stats['duration'] += duration
            if changed:
                host_stats['changed_operations'] += 1
            if failed:
                host_stats['failed_operations'] += 1

            stats['summary']['successful_operations'] = max(0, stats['summary']['total_operations'] - stats['summary']['failed_operations'])
            host_stats['successful_operations'] = max(0, host_stats['total_operations'] - host_stats['failed_operations'])

    @staticmethod
    def operation_host_start(state: State, host: Host, op_hash):
        """Records the start time of an operation on a specific host."""
        op_hash_context.set(op_hash)
        key = f"{host.name}:{op_hash}"
        ChaosTelemetry._timers[key] = time.time()

    @staticmethod
    def _parse_meta(meta: str) -> dict:
        vars = meta.split("(")[1].split(")")[0]
        executed = vars.split("executed=")[1].split(",")[0]
        maybeChange = vars.split("maybeChange=")[1].split(",")[0]
        hash = vars.split("hash")[1].split(",")[0]
        clean_executed = ChaosTelemetry._clean_value(executed)
        clean_maybe = ChaosTelemetry._clean_value(maybeChange)
        return {
            'executed': clean_executed,
            'maybe_change': clean_maybe,
            'hash': hash
        }

    @staticmethod
    def _clean_value(value: str):
        import ast
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    @staticmethod
    def _sanitize_op_data(raw_data) -> dict:
        """
        cleanse op data to remove sensitive information before logging
        """
        clean_data = {}

        IGNORED_KEYS = ['state', 'host', 'command_generator']

        SENSITIVE_TERMS = ['password', 'secret', 'token', 'key', 'auth', 'sudo_pass']

        for key, value in raw_data.items():
            if key in IGNORED_KEYS:
                continue

            elif key == 'global_arguments':
                clean_data[key] = ChaosTelemetry._sanitize_op_data(value)

            elif key == 'operation_meta':
                clean_data[key] = ChaosTelemetry._parse_meta(str(value))

            elif any(term in key.lower() for term in SENSITIVE_TERMS):
                clean_data[key] = "********"

            elif hasattr(value, '__call__'):
                clean_data[key] = "<function>"
            else:
                clean_data[key] = ChaosTelemetry._clean_value(value)

        return clean_data

    @staticmethod
    def operation_host_success(state: State, host: Host, op_hash, retry_count: int = 0):
        """Handles the successful completion of an operation on a specific host."""
        key = f"{host.name}:{op_hash}"
        start_time = ChaosTelemetry._timers.pop(key, None)
        duration = time.time() - start_time if start_time else 0.0

        state_meta: StateOperationMeta = state.get_op_meta(op_hash)
        op_name = list(state_meta.names)[0] if state_meta.names else "unknown_operation"

        op_data: StateOperationHostData = state.get_op_data_for_host(host, op_hash)
        runtime_meta: OperationMeta = op_data.operation_meta
        stdout, stderr = ChaosTelemetry._get_safe_logs(runtime_meta)

        logs = {
            'stdout': stdout,
            'stderr': stderr,
            'retry_attempts': runtime_meta.retry_attempts,
            'max_retries': runtime_meta.max_retries,
            'retry_info': runtime_meta.get_retry_info(),
        }

        changed = runtime_meta.changed

        raw_data = vars(op_data)
        operation_arguments = ChaosTelemetry._sanitize_op_data(raw_data)

        diff_log = ChaosTelemetry._diff_log_buffer.pop(op_hash, [])
        diff_text = "\n".join(diff_log) if diff_log else ""

        op_details = {
            'operation': op_name,
            'changed': changed,
            'success': True,
            'duration': round(duration, 4),
            'stdout': logs['stdout'],
            'stderr': logs['stderr'],
            'diff': diff_text,
            'operation_arguments': operation_arguments,
            'retry_statistics': logs,
        }

        ChaosTelemetry._stream_event(
            host, op_name, changed, False, retry_count, duration, logs, op_hash, diff_text,
            operation_arguments=operation_arguments,
            retry_statistics=logs
        )
        ChaosTelemetry._update_statistics(host, changed, False, duration, op_details)

    @staticmethod
    def operation_host_error(state: State, host: Host, op_hash, retry_count: int = 0, max_retries: int = 0):
        """Handles the failure of an operation on a specific host."""
        key = f"{host.name}:{op_hash}"
        start_time = ChaosTelemetry._timers.pop(key, None)
        duration = time.time() - start_time if start_time else 0.0

        static_meta = state.get_op_meta(op_hash)
        op_name = list(static_meta.names)[0] if static_meta.names else "Unknown Task"
        op_data = state.get_op_data_for_host(host, op_hash)

        raw_data = vars(op_data)
        operation_arguments = ChaosTelemetry._sanitize_op_data(raw_data)

        diff_log = ChaosTelemetry._diff_log_buffer.pop(op_hash, [])
        diff_text = "\n".join(diff_log) if diff_log else ""

        stdout, stderr = '', 'Operation Failed.'
        if hasattr(op_data, 'operation_meta') and op_data.operation_meta:
             s_out, s_err = ChaosTelemetry._get_safe_logs(op_data.operation_meta)
             if s_out or s_err:
                 stdout, stderr = s_out, s_err

        is_failure = True

        op_data: StateOperationHostData = state.get_op_data_for_host(host, op_hash)
        runtime_meta: OperationMeta = op_data.operation_meta

        logs = {
            'stdout': stdout,
            'stderr': stderr,
            'retry_attempts': runtime_meta.retry_attempts,
            'max_retries': runtime_meta.max_retries,
            'retry_info': runtime_meta.get_retry_info(),
        }

        op_details = {
            'operation': op_name,
            'changed': False,
            'success': False,
            'duration': round(duration, 4),
            'stdout': stdout,
            'stderr': stderr,
            'diff': diff_text,
            'operation_arguments': operation_arguments,
            'retry_statistics': logs,
        }

        ChaosTelemetry._stream_event(
            host, op_name, False, True, retry_count, duration, logs, op_hash, diff_text,
            operation_arguments=operation_arguments,
            retry_statistics=logs
        )
        ChaosTelemetry._update_statistics(host, False, is_failure, duration, op_details)

    @staticmethod
    def add_op_durations(op_events: list):
        """Gathers all operation durations from a list of operation events."""
        op_durations = {}
        for op in op_events:
            op_name = op.get('operation')
            duration = op.get('duration', 0.0)
            if op_name:
                if op_name not in op_durations:
                    op_durations[op_name] = []
                op_durations[op_name].append(duration)
        return op_durations

    @staticmethod
    def percentile(data: list, percentile_val: float):
        """Calculates the given percentile from a list of numbers."""
        if not data: return 0.0
        size = len(data)
        sorted_data = sorted(data)
        k = (size - 1) * (percentile_val / 100)
        f = int(k)
        c = k - f
        if f + 1 < size:
            return round(sorted_data[f] + (c * (sorted_data[f + 1] - sorted_data[f])), 4)
        else:
            return round(sorted_data[f], 4)

    @staticmethod
    def add_operation_percentiles(op_durations: dict):
        """Calculates and adds operation duration percentiles to the report data."""
        op_summary = {}
        for name, durations in op_durations.items():
            count = len(durations)
            total_duration = round(sum(durations), 4)
            op_summary[name] = {
                'count': count,
                'total_duration': total_duration,
                'average_duration': round(total_duration / count, 4) if count > 0 else 0.0,
                'p50_duration': ChaosTelemetry.percentile(durations, 50),
                'p90_duration': ChaosTelemetry.percentile(durations, 90),
                'p95_duration': ChaosTelemetry.percentile(durations, 95),
                'p99_duration': ChaosTelemetry.percentile(durations, 99),
            }
        ChaosTelemetry._report_data['operation_summary'] = op_summary

    @staticmethod
    def add_hailer_info():
        """Adds information about the hailer (the machine running Ch-aOS) to the report."""
        import os
        import socket
        hailer_info = {
            'user': os.getenv('USER') or os.getenv('USERNAME') or 'unknown',
            'boatswain': socket.gethostbyname(socket.gethostname()),
            'hostname': socket.gethostname(),
        }

        ChaosTelemetry._report_data['hailer'] = hailer_info

    @classmethod
    def _process_data(cls):
        if cls._temp_log_dir is None:
                return  # No logs were generated

        if hasattr(cls._thread_local, 'log_file_handle'):
            cls._thread_local.log_file_handle.close()

        all_events = []
        for temp_file in cls._temp_log_files:
            with open(temp_file, 'r') as f:
                for line in f:
                    try:
                        all_events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue # Ignore malformed lines

        all_events.sort(key=lambda x: x.get('timestamp', 0))

        final_report = cls._report_data
        final_report['resource_history'] = []
        final_report['fact_history'] = []
        # final_report['command_history'] = []
        final_report['streamed_history'] = []

        op_events_for_percentiles = []

        for host_name, host_data in final_report['hosts'].items():
            host_data['history'] = []

            for event in all_events:
                event_type = event.get('type')
                if event_type == 'progress':

                    for fact in event.get('facts_collected', []):
                        final_report['fact_history'].append(fact)

                    host_name = event.get('host')
                    if host_name in final_report['hosts']:
                        op_details = {
                            'operation': event.get('operation'),
                            'changed': event.get('changed'),
                            'success': event.get('success'),
                            'duration': event.get('duration'),
                            'stdout': event.get('logs', {}).get('stdout'),
                            'stderr': event.get('logs', {}).get('stderr'),
                            'diff': event.get('diff'),
                            'operation_arguments': event.get('operation_arguments'),
                            'retry_statistics': event.get('retry_statistics'),
                        }

                        final_report['hosts'][host_name]['history'].append(op_details)

                        op_events_for_percentiles.append(event)

                    final_report['streamed_history'].append(event)

                elif event_type == 'health_check':
                    final_report['resource_history'].append(event)

                elif event_type == 'fact_log_event':
                    log_entry = {
                        "timestamp": event.get('timestamp'),
                        "log_level": event.get('log_level'),
                        "context": event.get('context'),
                        "command": event.get('command'),
                    }

                    if event.get('context') == "fact_gathering":
                        final_report['fact_history'].append(log_entry)

                    # elif "running_command" in event.get('context', ''):
                    #     final_report['command_history'].append(log_entry)

                elif event_type == 'setup_phase':
                     for host_data in final_report['hosts'].values():
                        host_data['history'].insert(0, event)

            # final_report['command_history'].sort(key=lambda x: x.get('timestamp', 0))
            final_report['fact_history'].sort(key=lambda x: x.get('timestamp', 0))

            op_durations = cls.add_op_durations(op_events_for_percentiles)
            cls.add_operation_percentiles(op_durations)
            cls.add_hailer_info()
            final_report['operation_summary'] = cls._report_data['operation_summary']
            final_report['hailer'] = cls._report_data['hailer']
            return final_report

    @classmethod
    def export_report(cls, filepath: str = "chaos_logbook.json"):
        """
        Processes temporary log files to generate the final structured JSON report.
        """
        import shutil

        with cls._lock:
            final_report = cls._process_data()

            print(f"CHAOS_LOGBOOK::{json.dumps(final_report)}", flush=True)
            try:
                with open(filepath, 'w') as f:
                    json.dump(final_report, f, indent=4)

                logbook_dir = Path(os.path.expanduser("~/.local/share/chaos/logbooks"))
                if not logbook_dir.exists():
                    logbook_dir.mkdir(parents=True, exist_ok=True)

                amount = len(list(logbook_dir.glob("chaos_logbook_*.json")))
                shutil.copy(filepath, logbook_dir / f"chaos_logbook_run{amount+1}_{int(time.time())}.json")

            except Exception as e:
                print(f"Error writing final report: {e}")

            finally:
                shutil.rmtree(cls._temp_log_dir)
                cls._temp_log_dir = None
                cls._temp_log_files.clear()
                cls._thread_local = threading.local()

