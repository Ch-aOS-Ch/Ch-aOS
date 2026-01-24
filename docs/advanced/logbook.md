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

A LOT MORE BRO, I CAN'T FIT IT ALL HERE. SEE THE EXAMPLE AT THE BOTTOM, THERE'S TOO MUCH.

## Enabling/Disabling Logbook

Just run `chaos apply` together with `--logbook` to enable data collection for that specific execution. If you want to disable data collection, simply omit the `--logbook` flag when running the command. (it will still run, but no data data will be collected).

## Why?

Well, "Data collection" has a bad name to it doesn't it? People often associate telemetry with invasive data collection practices. However, in the case of Ch-aOS, telemetry is designed to enhance user experience and provide valuable insights into the operations performed.

It's important to note that telemetry in Ch-aOS is NEVER streamed to any external servers or third-party services. All telemetry data is stored locally on the user's machine in the `chaos_logbook.json` file AND inside of `~/.local/share/chaos/logbooks/`. This ensures that users have full control over their data and can choose to share it or not.

That being said, this data can be extremely useful for users who want to monitor and analyze the performance of their Ch-aOS operations. By collecting detailed information about each execution, users can gain insights into the efficiency of their workflows, identify potential bottlenecks, and make informed decisions about optimizing their processes. Plus, you know, Ch-apetanios, Ch-aOS' future centralized management self-hosted server, could use this data to provide better insights and reports to users managing multiple systems.

## Using Data

All data collected gets turned into a simple-to-read, simple-to-parse JSON file. This file can be easily integrated with monitoring systems like Prometheus, Grafana, or any other system that supports JSON data ingestion, or... you know, even your own brain to analyze the data manually.

Each operation performed during the `chaos apply -l` execution is also streamed to the stdout in real-time, allowing users to capture and parse the data as it is currently being generated.

## Privacy Considerations

Again, it's crucial to emphasize that all data collected by Ch-aOS is stored locally and is not transmitted to any external entities. Users have complete control over their data and can choose to share it or keep it private.

In case of the non use of the `--logbook` flag, no data is collected, ensuring that users who prioritize privacy can operate without any data collection concerns.

By providing these features, Ch-aOS aims to empower users with valuable insights while respecting their privacy and data ownership.

Stay safe.

### Example data collected (1 role, 1 host):

```json
{
    "hailer": {
        "user": "dexmachina",
        "boatswain": "...",
        "hostname": "Dionysus"
    },
    "hosts": {
        "@local": {
            "total_operations": 3,
            "changed_operations": 0,
            "successful_operations": 3,
            "failed_operations": 0,
            "duration": 1.4624347686767578,
            "history": [
                {
                    "type": "setup_phase",
                    "stage": "connection_and_facts",
                    "timestamp": 1769218393.5000405,
                    "duration": 0.0024,
                    "success": true
                },
                {
                    "operation": "Ensuring secrets state directory exists",
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
                            "name": "Ensuring secrets state directory exists",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=784a97bf1955d5f7a2b9dd6c1e371e17b73c42bc)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 0.3348,
                    "stdout": "",
                    "stderr": "",
                    "fact_logs": [],
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
                    "operation": "Recording new secrets state",
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
                            "name": "Recording new secrets state",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=9c1c01dc3ac1445a500251fc34a15d3e75a849df)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 1.0835,
                    "stdout": "",
                    "stderr": "",
                    "fact_logs": [],
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
                    "operation": "Deploy secret template to /home/dexmachina/esse_arquivo.txt for user dexmachina",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": "True",
                            "_sudo_user": "dexmachina",
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
                            "name": "Deploy secret template to /home/dexmachina/esse_arquivo.txt for user dexmachina",
                            "_ignore_errors": "False",
                            "_continue_on_error": "False",
                            "_if": "[]"
                        },
                        "operation_meta": "OperationMeta(executed=False, maybeChange=False, hash=f4f59e822581d785ba910fbf3f268eca79db8204)"
                    },
                    "changed": false,
                    "success": true,
                    "duration": 0.0441,
                    "stdout": "",
                    "stderr": "",
                    "fact_logs": [],
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
    "summary": {
        "total_operations": 3,
        "changed_operations": 0,
        "successful_operations": 3,
        "failed_operations": 0,
        "status": "success",
        "total_duration": 1.4624347686767578
    },
    "resource_history": [
        {
            "type": "health_check",
            "host": "@local",
            "stage": "pre_operations",
            "timestamp": 1769218393.5060794,
            "metrics": {
                "cpu_load_1min": 0.69,
                "cpu_load_5min": 0.89,
                "ram_percent": 32.8,
                "ram_used_gb": 5.04,
                "ram_total_gb": 15.37
            }
        },
        {
            "type": "health_check",
            "host": "@local",
            "stage": "post_operations",
            "timestamp": 1769218400.9945695,
            "metrics": {
                "cpu_load_1min": 0.63,
                "cpu_load_5min": 0.87,
                "ram_percent": 32.6,
                "ram_used_gb": 5.01,
                "ram_total_gb": 15.37
            }
        }
    ],
    "command_history": [
        {
            "timestamp": 1769218399.5248134,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
        },
        {
            "timestamp": 1769218399.8598616,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
        },
        {
            "timestamp": 1769218400.1469924,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
        },
        {
            "timestamp": 1769218400.614431,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769218400.9435391,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/esse_arquivo.txt || test -L /home/dexmachina/esse_arquivo.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/esse_arquivo.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/esse_arquivo.txt || ls -ld /home/dexmachina/esse_arquivo.txt )'"
        },
        {
            "timestamp": 1769218400.9572306,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
        },
        {
            "timestamp": 1769218400.974607,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/esse_arquivo.txt && ( sha1sum /home/dexmachina/esse_arquivo.txt 2> /dev/null || shasum /home/dexmachina/esse_arquivo.txt 2> /dev/null || sha1 /home/dexmachina/esse_arquivo.txt 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769218400.9875813,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "sh -c 'cat /proc/meminfo'"
        },
        {
            "timestamp": 1769218400.9914162,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "sh -c 'cat /proc/loadavg'"
        }
    ],
    "fact_history": [
        {
            "timestamp": 1769218393.5013716,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218393.504108,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218393.652952,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=cat /var/lib/chaos/secrets.yml || true) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218395.5687594,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218396.0467238,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218398.6831975,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.1143124,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.482103,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Home (user=dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.4849067,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/esse_arquivo.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.4981964,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.5112858,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/esse_arquivo.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.5245965,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218399.8597257,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.1468632,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.6142983,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.9434094,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/esse_arquivo.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.957026,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.9743657,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/esse_arquivo.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.9875324,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769218400.9913502,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        }
    ],
    "streamed_history": [
        {
            "type": "progress",
            "host": "@local",
            "operation": "Ensuring secrets state directory exists",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 0.3348195552825928,
            "operation_commands": [
                {
                    "timestamp": 1769218399.5245965,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218399.5248134,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                }
            ],
            "logs": {
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
            "type": "progress",
            "host": "@local",
            "operation": "Recording new secrets state",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 1.0835397243499756,
            "operation_commands": [
                {
                    "timestamp": 1769218399.8597257,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218399.8598616,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
                },
                {
                    "timestamp": 1769218400.1468632,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218400.1469924,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                },
                {
                    "timestamp": 1769218400.6142983,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218400.614431,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
                }
            ],
            "logs": {
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
            "type": "progress",
            "host": "@local",
            "operation": "Deploy secret template to /home/dexmachina/esse_arquivo.txt for user dexmachina",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 0.04407548904418945,
            "operation_commands": [
                {
                    "timestamp": 1769218400.9434094,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/home/dexmachina/esse_arquivo.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218400.9435391,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/esse_arquivo.txt || test -L /home/dexmachina/esse_arquivo.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/esse_arquivo.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/esse_arquivo.txt || ls -ld /home/dexmachina/esse_arquivo.txt )'"
                },
                {
                    "timestamp": 1769218400.957026,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218400.9572306,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                },
                {
                    "timestamp": 1769218400.9743657,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/home/dexmachina/esse_arquivo.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769218400.974607,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-dRYxuQ7FN4cV *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/esse_arquivo.txt && ( sha1sum /home/dexmachina/esse_arquivo.txt 2> /dev/null || shasum /home/dexmachina/esse_arquivo.txt 2> /dev/null || sha1 /home/dexmachina/esse_arquivo.txt 2> /dev/null ) || true'"
                }
            ],
            "logs": {
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
    ],
    "operation_summary": {
        "Ensuring secrets state directory exists": {
            "count": 1,
            "total_duration": 0.3348,
            "average_duration": 0.3348,
            "p50_duration": 0.3348,
            "p90_duration": 0.3348,
            "p95_duration": 0.3348,
            "p99_duration": 0.3348
        },
        "Recording new secrets state": {
            "count": 1,
            "total_duration": 1.0835,
            "average_duration": 1.0835,
            "p50_duration": 1.0835,
            "p90_duration": 1.0835,
            "p95_duration": 1.0835,
            "p99_duration": 1.0835
        },
        "Deploy secret template to /home/dexmachina/esse_arquivo.txt for user dexmachina": {
            "count": 1,
            "total_duration": 0.0441,
            "average_duration": 0.0441,
            "p50_duration": 0.0441,
            "p90_duration": 0.0441,
            "p95_duration": 0.0441,
            "p99_duration": 0.0441
        }
    }
}
```
