# Ch-aOS Logbook

The `chaos apply` command includes a built-in observability feature that collects data about the operations performed. This information is optionally used to help users integrate the project with monitoring systems.

It saves all data related to a specific `chaos apply` execution in a JSON file located at `./chaos_report.json`. This file contains detailed information about the execution, including:

  - total run operations,

  -  number of changed operations,

  - number of successful and failed operations,

  - total run time,

  - run status,

  - hosts:

    - host name,

    - operations performed on the host,

    - successful and failed operations per host,

    - time taken per host.

    - history:

      - name of the operation,

      - if the operation was a success,

      - stdout and stderr outputs,

      - retry statistics

## Enabling/Disabling Logbook

Just run `chaos apply` together with `--logbook` to enable data collection for that specific execution. If you want to disable data collection, simply omit the `--logbook` flag when running the command. (it will still run, but no data data will be collected).

## Why?

Well, "Data collection" has a bad name to it doesn't it? People often associate telemetry with invasive data collection practices. However, in the case of Ch-aOS, telemetry is designed to enhance user experience and provide valuable insights into the operations performed.

It's important to note that telemetry in Ch-aOS is NEVER streamed to any external servers or third-party services. All telemetry data is stored locally on the user's machine in the `chaos_logbook.json` file AND inside of `~/.local/share/chaos/logbooks/`. This ensures that users have full control over their data and can choose to share it or not.

That being said, this data can be extremely useful for users who want to monitor and analyze the performance of their Ch-aOS operations. By collecting detailed information about each execution, users can gain insights into the efficiency of their workflows, identify potential bottlenecks, and make informed decisions about optimizing their processes. Plus, you know, Ch-apetanios, Ch-aOS' future centralized management self-hosted server, could use this data to provide better insights and reports to users managing multiple systems.

## Using Data

All data collected gets turned into a simple-to-read, simple-to-parse JSON file. This file can be easily integrated with monitoring systems like Prometheus, Grafana, or any other system that supports JSON data ingestion, or... you know, even your own brain to analyze the data manually.

## Privacy Considerations

Again, it's crucial to emphasize that all data collected by Ch-aOS is stored locally and is not transmitted to any external entities. Users have complete control over their data and can choose to share it or keep it private.

In case of the non use of the `--logbook` flag, no data is collected, ensuring that users who prioritize privacy can operate without any data collection concerns.

By providing these features, Ch-aOS aims to empower users with valuable insights while respecting their privacy and data ownership.

Stay safe.

### Example data collected (1 role, 1 host):

```json
{
    "summary": {
        "total_operations": 5,
        "changed_operations": 1,
        "successful_operations": 5,
        "failed_operations": 0,
        "status": "success",
        "total_duration": 6.550549507141113
    },
    "hailer": {
        "user": "dexmachina",
        "boatswain": "192.168.1.2",
        "hostname": "Dionysus"
    },
    "hosts": {
        "@local": {
            "total_operations": 5,
            "changed_operations": 1,
            "successful_operations": 5,
            "failed_operations": 0,
            "duration": 6.550549507141113,
            "history": [
                {
                    "type": "setup_phase",
                    "stage": "connection_and_facts",
                    "timestamp": 1768881124.799683,
                    "duration": 3.0237,
                    "success": true
                },
                {
                    "operation": "Ensure sudo rule 99-charonte-dexmachina",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": "True",
                            "_use_sudo_login": "False",
                            "_sudo_password": "********",
                            "_preserve_sudo_env": "False",
                            "_use_su_login": "False",
                            "_preserve_su_env": "False",
                            "_su_shell": "False",
                            "_doas": "False",
                            "_shell_executable": "sh",
                            "_env": "{}",
                            "_success_exit_codes": "[0]",
                            "_get_pty": "False",
                            "_retries": "0",
                            "_retry_delay": "5",
                            "name": "Ensure sudo rule 99-charonte-dexmachina",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=784a97bf1955d5f7a2b9dd6c1e371e17b73c42bc)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 1.1187,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_info": {
                            "retry_attempts": 0,
                            "max_retries": 0,
                            "was_retried": false,
                            "retry_succeeded": null
                        }
                    }
                },
                {
                    "operation": "Validate sudo rule 99-charonte-dexmachina",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": "True",
                            "_use_sudo_login": "False",
                            "_sudo_password": "********",
                            "_preserve_sudo_env": "False",
                            "_use_su_login": "False",
                            "_preserve_su_env": "False",
                            "_su_shell": "False",
                            "_doas": "False",
                            "_shell_executable": "sh",
                            "_env": "{}",
                            "_success_exit_codes": "[0]",
                            "_get_pty": "False",
                            "_retries": "0",
                            "_retry_delay": "5",
                            "name": "Validate sudo rule 99-charonte-dexmachina",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=True, hash=9c1c01dc3ac1445a500251fc34a15d3e75a849df)"
                    },
                    "changed": true,
                    "success": true,
                    "duration": 0.4154,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_info": {
                            "retry_attempts": 0,
                            "max_retries": 0,
                            "was_retried": false,
                            "retry_succeeded": null
                        }
                    }
                },
                {
                    "operation": "server.group",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": "True",
                            "_use_sudo_login": "False",
                            "_sudo_password": "********",
                            "_preserve_sudo_env": "False",
                            "_use_su_login": "False",
                            "_preserve_su_env": "False",
                            "_su_shell": "False",
                            "_doas": "False",
                            "_shell_executable": "sh",
                            "_env": "{}",
                            "_success_exit_codes": "[0]",
                            "_get_pty": "False",
                            "_retries": "0",
                            "_retry_delay": "5",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=f4f59e822581d785ba910fbf3f268eca79db8204)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 0.7984,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_info": {
                            "retry_attempts": 0,
                            "max_retries": 0,
                            "was_retried": false,
                            "retry_succeeded": null
                        }
                    }
                },
                {
                    "operation": "server.group",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": "True",
                            "_use_sudo_login": "False",
                            "_sudo_password": "********",
                            "_preserve_sudo_env": "False",
                            "_use_su_login": "False",
                            "_preserve_su_env": "False",
                            "_su_shell": "False",
                            "_doas": "False",
                            "_shell_executable": "sh",
                            "_env": "{}",
                            "_success_exit_codes": "[0]",
                            "_get_pty": "False",
                            "_retries": "0",
                            "_retry_delay": "5",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=08743582456b52abe1182f5a5a3e12b457ba28b8)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 2.3203,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_info": {
                            "retry_attempts": 0,
                            "max_retries": 0,
                            "was_retried": false,
                            "retry_succeeded": null
                        }
                    }
                },
                {
                    "operation": "server.user",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": "True",
                            "_use_sudo_login": "False",
                            "_sudo_password": "********",
                            "_preserve_sudo_env": "False",
                            "_use_su_login": "False",
                            "_preserve_su_env": "False",
                            "_su_shell": "False",
                            "_doas": "False",
                            "_shell_executable": "sh",
                            "_env": "{}",
                            "_success_exit_codes": "[0]",
                            "_get_pty": "False",
                            "_retries": "0",
                            "_retry_delay": "5",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=6a58b6c7e02f6d92150e84bffa4418d987f54dc9)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 1.8978,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_info": {
                            "retry_attempts": 0,
                            "max_retries": 0,
                            "was_retried": false,
                            "retry_succeeded": null
                        }
                    }
                }
            ]
        }
    },
    "resource_history": [
        {
            "type": "health_check",
            "host": "@local",
            "stage": "pre_operations",
            "timestamp": 1768881124.8052301,
            "metrics": {
                "cpu_load_1min": 1.53,
                "cpu_load_5min": 1.4,
                "ram_percent": 53.1,
                "ram_used_gb": 8.15,
                "ram_total_gb": 15.37
            }
        },
        {
            "type": "health_check",
            "host": "@local",
            "stage": "post_operations",
            "timestamp": 1768881140.6177595,
            "metrics": {
                "cpu_load_1min": 1.46,
                "cpu_load_5min": 1.39,
                "ram_percent": 53.1,
                "ram_used_gb": 8.16,
                "ram_total_gb": 15.37
            }
        }
    ],
    "operation_summary": {
        "Ensure sudo rule 99-charonte-dexmachina": {
            "count": 1,
            "total_duration": 1.1187,
            "average_duration": 1.1187,
            "p50_duration": 1.1187,
            "p90_duration": 1.1187,
            "p95_duration": 1.1187,
            "p99_duration": 1.1187
        },
        "Validate sudo rule 99-charonte-dexmachina": {
            "count": 1,
            "total_duration": 0.4154,
            "average_duration": 0.4154,
            "p50_duration": 0.4154,
            "p90_duration": 0.4154,
            "p95_duration": 0.4154,
            "p99_duration": 0.4154
        },
        "server.group": {
            "count": 2,
            "total_duration": 3.1187,
            "average_duration": 1.5594,
            "p50_duration": 1.5594,
            "p90_duration": 2.1681,
            "p95_duration": 2.2442,
            "p99_duration": 2.3051
        },
        "server.user": {
            "count": 1,
            "total_duration": 1.8978,
            "average_duration": 1.8978,
            "p50_duration": 1.8978,
            "p90_duration": 1.8978,
            "p95_duration": 1.8978,
            "p99_duration": 1.8978
        }
    }
}
```
