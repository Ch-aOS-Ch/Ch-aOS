# Ch-aOS Telemetry

The `chaos apply` command includes a built-in observability feature that collects telemetry data about the operations performed. This information is optionally used to help users integrate the project with monitoring systems.

It saves all telemetry data related to a specific `chaos apply` execution in a JSON file located at `./chaos_report.json`. This file contains detailed information about the execution, including:

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

## Enabling/Disabling Telemetry

Just run `chaos apply` together with `--logbook` to enable telemetry collection for that specific execution. If you want to disable telemetry collection, simply omit the `--logbook` flag when running the command. (it will still run, but no telemetry data will be collected).

## Why Telemetry?

Well, telemetry has a bad name to it doesn't it? People often associate telemetry with invasive data collection practices. However, in the case of Ch-aOS, telemetry is designed to enhance user experience and provide valuable insights into the operations performed.

It's important to note that telemetry in Ch-aOS is NEVER streamed to any external servers or third-party services. All telemetry data is stored locally on the user's machine in the `chaos_report.json` file. This ensures that users have full control over their data and can choose to share it or not.

That being said, telemetry data can be extremely useful for users who want to monitor and analyze the performance of their Ch-aOS operations. By collecting detailed information about each execution, users can gain insights into the efficiency of their workflows, identify potential bottlenecks, and make informed decisions about optimizing their processes. Plus, you know, Ch-apetanios, Ch-aOS' future centralized management self-hosted server, could use this data to provide better insights and reports to users managing multiple systems.

## Using Telemetry Data

All telemetry collected gets turned into a simple-to-read, simple-to-parse JSON file. This file can be easily integrated with monitoring systems like Prometheus, Grafana, or any other system that supports JSON data ingestion, or... you know, even your own brain to analyze the data manually.

## Privacy Considerations

Again, it's crucial to emphasize that telemetry data collected by Ch-aOS is stored locally and is not transmitted to any external entities. Users have complete control over their telemetry data and can choose to share it or keep it private.

In case of the non use of the `--logbook` flag, no telemetry data is collected, ensuring that users who prioritize privacy can operate without any data collection concerns.

By providing telemetry features, Ch-aOS aims to empower users with valuable insights while respecting their privacy and data ownership.

Never allow anyone tell you telemetry is bad. It's all about how it's implemented and used!

Stay safe.

### Example telemetry collected (1 role, 1 host):

```json
{
    "summary": {
        "total_operations": 5,
        "changed_operations": 1,
        "successful_operations": 5,
        "failed_operations": 0,
        "status": "success",
        "total_duration": 3.7454774379730225
    },
    "hosts": {
        "@local": {
            "total_operations": 5,
            "changed_operations": 1,
            "successful_operations": 5,
            "failed_operations": 0,
            "duration": 3.7454774379730225,
            "history": [
                {
                    "operation": "Ensure sudo rule 99-charonte-dexmachina",
                    "changed": false,
                    "success": true,
                    "duration": 0.9548,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_succeeded": null,
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
                    "changed": true,
                    "success": true,
                    "duration": 0.3911,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_succeeded": null,
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
                    "changed": false,
                    "success": true,
                    "duration": 0.575,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_succeeded": null,
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
                    "changed": false,
                    "success": true,
                    "duration": 0.5165,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_succeeded": null,
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
                    "changed": false,
                    "success": true,
                    "duration": 1.3081,
                    "stdout": "",
                    "stderr": "",
                    "retry_statistics": {
                        "stdout": "",
                        "stderr": "",
                        "retry_attempts": 0,
                        "max_retries": 0,
                        "retry_succeeded": null,
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
    }
}
```
