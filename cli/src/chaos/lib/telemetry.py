import json
import time
from pyinfra.api.operation import OperationMeta
from pyinfra.api.state import State, BaseStateCallback, StateOperationHostData, StateOperationMeta
from pyinfra.api.host import Host

class ChaosTelemetry(BaseStateCallback):
    """
    A telemetry system for tracking operation execution details in pyinfra-based chaos engineering experiments.
    This class captures detailed information about each operation performed on hosts, including
    whether the operation resulted in changes, succeeded, or failed. It also records execution duration
    and logs (stdout and stderr) associated with each operation.

    Key Features:
    - Operation Timing: Measures the duration of each operation on a per-host basis.

    - Event Streaming: Streams real-time progress events to standard output, which can be captured by
        external systems for monitoring or logging purposes.

    - Statistics Tracking: Maintains comprehensive statistics at both the summary level and per-host level,
        including total operations, changed operations, successful operations, failed operations, and total duration.

    - Detailed Logging: Captures and stores stdout and stderr logs for each operation, along with
        retry information if applicable.

    - Report Generation: Provides functionality to export a detailed report of all operations
        Executed during the chaos experiment to a JSON file.
    """

    _process = None
    _timers = {}
    _report_data = {
        'summary': {
            'total_operations': 0,
            'changed_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'status': 'success',
            'total_duration': 0.0,
        },
        'hailer': {},
        'hosts': {},
        'streamed_history': [],
        'resource_history': [],
        'operation_summary': {}
    }

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

        for host in state.inventory.iter_activated_hosts():
            if host.name not in ChaosTelemetry._report_data['hosts']:
                ChaosTelemetry._report_data['hosts'][host.name] = {
                    'total_operations': 0,
                    'changed_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'duration': 0.0,
                    'history': []
                }

            ChaosTelemetry._report_data['hosts'][host.name]['history'].insert(0, setup_event)
            print(f"CHAOS_EVENT::{json.dumps(setup_event)}", flush=True)

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

        print(f"CHAOS_EVENT::{json.dumps(snapshot)}", flush=True)
        ChaosTelemetry._report_data['resource_history'].append(snapshot)
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

    @staticmethod
    def _stream_event(host: Host, op_name, changed: bool, failed: bool, retry_count: int = 0, duration: float = 0.0, logs: dict = {}):
        """
        Streams a progress event to standard output in JSON format.

        This is useful for real-time monitoring of operation execution.
        Good for integrating with external logging or monitoring systems.

        Optionally, includes an way to save the event history, not currently used because of
        hosts history tracking.
        """

        payload = {
            "type": "progress",
            "host": host.name,
            "operation": op_name,
            "changed": changed,
            "success": not failed,
            'retry_count': retry_count,
            'duration': duration,
            'logs': logs,
        }

        print(f"CHAOS_EVENT::{json.dumps(payload)}", flush=True)
        _report = ChaosTelemetry._report_data
        _report['streamed_history'].append(payload)

    @staticmethod
    def _update_statistics(host: Host, changed: bool, failed: bool, duration: float, op_details: dict):
        """
        Updates the telemetry statistics with the results of an operation executed on a host.

        This method updates both the summary statistics and the per-host statistics,
        including counts of total operations, changed operations, successful operations,
        failed operations, and total duration.

        Basically used for generating the final report.

        "Why not just use the streamed events?" - Because we want to avoid parsing
        "Why not just use pyinfra's StateHostResults?" - Because we want to track more detailed info like logs
        + We need _overall_ summary stats, not just per-host stats.
        + We want to avoid relying on pyinfra internals that may change.
        + pyinfra only tracks amount of ops, success/failure/ignore_errors/partial_ops, not detailed info we want.
        + We need a way to track changed operations specifically.
        + Since we use streaming events, the logic for implementing this would make it so we'd have to re-get all info
        from pyinfra's StateHostResults anyway, so might as well just track it here directly.
        """

        stats = ChaosTelemetry._report_data
        if host.name not in stats['hosts']:
            stats['hosts'][host.name] = {
                'total_operations': 0,
                'changed_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'duration': 0.0,
                'history': []
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

        host_stats['history'].append(op_details)

        stats['summary']['successful_operations'] = max(0, stats['summary']['total_operations'] - stats['summary']['failed_operations'])
        host_stats['successful_operations'] = max(0, host_stats['total_operations'] - host_stats['failed_operations'])

    @staticmethod
    def operation_host_start(state: State, host: Host, op_hash):
        """Records the start time of an operation on a specific host."""
        key = f"{host.name}:{op_hash}"
        ChaosTelemetry._timers[key] = time.time()

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

            if key == 'global_arguments':
                clean_data[key] = ChaosTelemetry._sanitize_op_data(value)
                continue

            if any(term in key.lower() for term in SENSITIVE_TERMS):
                clean_data[key] = "********"
                continue

            if value is None:
                continue

            if hasattr(value, '__call__'):
                clean_data[key] = "<function>"
            else:
                clean_data[key] = str(value)

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

        op_details = {
            'operation': op_name,
            'operation_arguments': operation_arguments,
            'changed': changed,
            'success': True,
            'duration': round(duration, 4),
            'stdout': logs['stdout'],
            'stderr': logs['stderr'],
            'retry_statistics': logs,
        }

        ChaosTelemetry._stream_event(host, op_name, changed, False, retry_count)
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

        stdout, stderr = '', 'Operation Failed.'
        if hasattr(op_data, 'operation_meta') and op_data.operation_meta:
             s_out, s_err = ChaosTelemetry._get_safe_logs(op_data.operation_meta)
             if s_out or s_err:
                 stdout, stderr = s_out, s_err

        is_failure = True
        if hasattr(op_data, 'global_arguments'):
             is_failure = not getattr(op_data.global_arguments, 'ignore_errors', False)

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
            'retry_statistics': logs,
        }

        ChaosTelemetry._stream_event(host, op_name, False, is_failure)
        ChaosTelemetry._update_statistics(host, False, is_failure, duration, op_details)

    @staticmethod
    def add_op_durations():
        """Gathers all operation durations from the report history."""
        op_durations = {}
        for host_data in ChaosTelemetry._report_data['hosts'].values():
            for op in host_data.get('history', []):
                if 'operation' in op:
                    op_name = op['operation']
                    duration = op.get('duration', 0.0)
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
    def export_report(cls, filepath: str = "chaos_logbook.json"):
        """Exports the collected data to a JSON file and prints it to standard output."""
        from pathlib import Path
        import os
        import time
        import shutil
        op_durations = cls.add_op_durations()
        cls.add_operation_percentiles(op_durations)
        cls.add_hailer_info()

        print(f"CHAOS_LOGBOOK::{json.dumps(cls._report_data)}", flush=True)
        try:
            with open(filepath, 'w') as f:
                json.dump(cls._report_data, f, indent=4)
            logbook_dir = Path(os.path.expanduser("~/.local/share/chaos/logbooks"))
            if not logbook_dir.exists():
                logbook_dir.mkdir(parents=True, exist_ok=True)
            amount = len(list(logbook_dir.glob("chaos_logbook_*.json")))
            shutil.copy(filepath, logbook_dir / f"chaos_logbook_run{amount+1}_{int(time.time())}.json")
        except Exception:
            pass
