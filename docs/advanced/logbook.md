# Ch-aOS Logbook

The `chaos apply` command includes a built-in observability feature that collects data about the operations performed. This information is optionally used to help users integrate the project with monitoring systems.

It's important to note that the logbook pulls absolutely, completely and undoubtedly 0 punches. It has complete operation reconstruction from fact gathering to command execution with UNIX timestamps and multi-host support. It is feature complete, even with log streaming for real-time analysis.

Moreover, It is completely optional, and is only enabled by:

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
    "api_version": "v1",
    "hailer": {
        "user": "dexmachina",
        "boatswain": "...",
        "hostname": "Dionysus"
    },
    "hosts": {
        "@local": {
            "total_operations": 5,
            "changed_operations": 1,
            "successful_operations": 5,
            "failed_operations": 0,
            "duration": 4.865419149398804,
            "history": [
                {
                    "type": "setup_phase",
                    "stage": "connection_and_facts",
                    "timestamp": 1769283344.1297991,
                    "duration": 0.0024,
                    "success": true
                },
                {
                    "operation": "Ensure sudo rule 99-charonte-dexmachina",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": true,
                            "_sudo_user": null,
                            "_use_sudo_login": false,
                            "_sudo_password": "********",
                            "_preserve_sudo_env": false,
                            "_su_user": null,
                            "_use_su_login": false,
                            "_preserve_su_env": false,
                            "_su_shell": false,
                            "_doas": false,
                            "_doas_user": null,
                            "_shell_executable": "sh",
                            "_chdir": null,
                            "_env": {},
                            "_success_exit_codes": [
                                0
                            ],
                            "_timeout": null,
                            "_get_pty": false,
                            "_stdin": null,
                            "_retries": 0,
                            "_retry_delay": 5,
                            "_retry_until": null,
                            "name": "Ensure sudo rule 99-charonte-dexmachina",
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": false,
                            "hash": "=784a97bf1955d5f7a2b9dd6c1e371e17b73c42bc"
                        },
                        "parent_op_hash": null
                    },
                    "changed": false,
                    "success": true,
                    "duration": 1.2744,
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
                            "_sudo": true,
                            "_sudo_user": null,
                            "_use_sudo_login": false,
                            "_sudo_password": "********",
                            "_preserve_sudo_env": false,
                            "_su_user": null,
                            "_use_su_login": false,
                            "_preserve_su_env": false,
                            "_su_shell": false,
                            "_doas": false,
                            "_doas_user": null,
                            "_shell_executable": "sh",
                            "_chdir": null,
                            "_env": {},
                            "_success_exit_codes": [
                                0
                            ],
                            "_timeout": null,
                            "_get_pty": false,
                            "_stdin": null,
                            "_retries": 0,
                            "_retry_delay": 5,
                            "_retry_until": null,
                            "name": "Validate sudo rule 99-charonte-dexmachina",
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": true,
                            "hash": "=9c1c01dc3ac1445a500251fc34a15d3e75a849df"
                        },
                        "parent_op_hash": null
                    },
                    "changed": true,
                    "success": true,
                    "duration": 0.4153,
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
                            "_sudo": true,
                            "_sudo_user": null,
                            "_use_sudo_login": false,
                            "_sudo_password": "********",
                            "_preserve_sudo_env": false,
                            "_su_user": null,
                            "_use_su_login": false,
                            "_preserve_su_env": false,
                            "_su_shell": false,
                            "_doas": false,
                            "_doas_user": null,
                            "_shell_executable": "sh",
                            "_chdir": null,
                            "_env": {},
                            "_success_exit_codes": [
                                0
                            ],
                            "_timeout": null,
                            "_get_pty": false,
                            "_stdin": null,
                            "_retries": 0,
                            "_retry_delay": 5,
                            "_retry_until": null,
                            "name": null,
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": false,
                            "hash": "=f4f59e822581d785ba910fbf3f268eca79db8204"
                        },
                        "parent_op_hash": null
                    },
                    "changed": false,
                    "success": true,
                    "duration": 0.8033,
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
                            "_sudo": true,
                            "_sudo_user": null,
                            "_use_sudo_login": false,
                            "_sudo_password": "********",
                            "_preserve_sudo_env": false,
                            "_su_user": null,
                            "_use_su_login": false,
                            "_preserve_su_env": false,
                            "_su_shell": false,
                            "_doas": false,
                            "_doas_user": null,
                            "_shell_executable": "sh",
                            "_chdir": null,
                            "_env": {},
                            "_success_exit_codes": [
                                0
                            ],
                            "_timeout": null,
                            "_get_pty": false,
                            "_stdin": null,
                            "_retries": 0,
                            "_retry_delay": 5,
                            "_retry_until": null,
                            "name": null,
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": false,
                            "hash": "=08743582456b52abe1182f5a5a3e12b457ba28b8"
                        },
                        "parent_op_hash": null
                    },
                    "changed": false,
                    "success": true,
                    "duration": 0.7676,
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
                            "_sudo": true,
                            "_sudo_user": null,
                            "_use_sudo_login": false,
                            "_sudo_password": "********",
                            "_preserve_sudo_env": false,
                            "_su_user": null,
                            "_use_su_login": false,
                            "_preserve_su_env": false,
                            "_su_shell": false,
                            "_doas": false,
                            "_doas_user": null,
                            "_shell_executable": "sh",
                            "_chdir": null,
                            "_env": {},
                            "_success_exit_codes": [
                                0
                            ],
                            "_timeout": null,
                            "_get_pty": false,
                            "_stdin": null,
                            "_retries": 0,
                            "_retry_delay": 5,
                            "_retry_until": null,
                            "name": null,
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": false,
                            "hash": "=6a58b6c7e02f6d92150e84bffa4418d987f54dc9"
                        },
                        "parent_op_hash": null
                    },
                    "changed": false,
                    "success": true,
                    "duration": 1.6048,
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
    "summary": {
        "total_operations": 5,
        "changed_operations": 1,
        "successful_operations": 5,
        "failed_operations": 0,
        "status": "success",
        "total_duration": 4.865419149398804
    },
    "resource_history": [
        {
            "type": "health_check",
            "host": "@local",
            "stage": "pre_operations",
            "timestamp": 1769283344.1355467,
            "metrics": {
                "cpu_load_1min": 0.75,
                "cpu_load_5min": 0.64,
                "ram_percent": 42.9,
                "ram_used_gb": 6.58,
                "ram_total_gb": 15.37
            }
        },
        {
            "type": "health_check",
            "host": "@local",
            "stage": "post_operations",
            "timestamp": 1769283355.3631995,
            "metrics": {
                "cpu_load_1min": 0.64,
                "cpu_load_5min": 0.62,
                "ram_percent": 42.6,
                "ram_used_gb": 6.54,
                "ram_total_gb": 15.37
            }
        }
    ],
    "command_history": [
        {
            "timestamp": 1769283350.4924953,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /etc/sudoers.d/99-charonte-dexmachina || test -L /etc/sudoers.d/99-charonte-dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /etc/sudoers.d/99-charonte-dexmachina || ls -ld /etc/sudoers.d/99-charonte-dexmachina )'"
        },
        {
            "timestamp": 1769283350.9429545,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /etc/sudoers.d || test -L /etc/sudoers.d ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /etc/sudoers.d 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /etc/sudoers.d || ls -ld /etc/sudoers.d )'"
        },
        {
            "timestamp": 1769283351.3872619,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'test -e /etc/sudoers.d/99-charonte-dexmachina && ( sha1sum /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || shasum /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || sha1 /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769283351.7668397,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'visudo -c -f /etc/sudoers.d/99-charonte-dexmachina'"
        },
        {
            "timestamp": 1769283352.1826324,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
        },
        {
            "timestamp": 1769283352.5135996,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
        },
        {
            "timestamp": 1769283352.9861417,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
        },
        {
            "timestamp": 1769283353.3532543,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
        },
        {
            "timestamp": 1769283353.7540562,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'for i in `cat /etc/passwd | cut -d: -f1`; do\n            ENTRY=`grep ^$i: /etc/passwd`;\n            LASTLOG=`(((lastlog -u $i || lastlogin $i) 2> /dev/null) | grep ^$i | tr -s '\"'\"' '\"'\"')`;\n            PASSWORD=`(grep ^$i: /etc/shadow || grep ^$i: /etc/master.passwd) 2> /dev/null | cut -d: -f2`;\n            echo \"$ENTRY|`id -gn $i`|`id -Gn $i`|$LASTLOG|$PASSWORD\";\n        done'"
        },
        {
            "timestamp": 1769283354.3316107,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
        },
        {
            "timestamp": 1769283354.7419145,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
        },
        {
            "timestamp": 1769283355.1060386,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
        },
        {
            "timestamp": 1769283355.3591557,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "sh -c 'cat /proc/meminfo'"
        },
        {
            "timestamp": 1769283355.36148,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "sh -c 'cat /proc/loadavg'"
        }
    ],
    "fact_history": [
        {
            "timestamp": 1769283344.1306696,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283344.1335003,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283344.3140237,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=awk -F: '($3>=1000 && $7 ~ /(bash|zsh|fish|sh)$/){print $1}' /etc/passwd) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283344.3172941,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=awk -F: '($3<1000){print $1}' /etc/passwd) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283344.3208873,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=find /etc/sudoers.d/ -type f -name '99-charonte-*' -printf '%f\n') (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283346.2189002,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283346.779401,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/etc/sudoers.d) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283347.0662026,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283347.335263,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Groups () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283348.0377762,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Os () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283348.3058684,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Groups () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283348.5773158,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Os () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283348.8177865,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Users () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283349.4835556,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Groups () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283349.7342293,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Os () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283350.0660543,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283350.4923735,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283350.9428334,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/etc/sudoers.d) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283351.3870976,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283352.1825817,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Groups () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283352.5135427,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Os () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283352.9860904,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Groups () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283353.3531942,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Os () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283353.7540016,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Users () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283354.3315556,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Groups () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283354.741862,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Os () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283355.10591,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283355.3590994,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769283355.3614388,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        }
    ],
    "streamed_history": [
        {
            "type": "progress",
            "host": "@local",
            "operation": "Ensure sudo rule 99-charonte-dexmachina",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 1.2744176387786865,
            "facts_collected": [
                {
                    "timestamp": 1769283350.4923735,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283350.9428334,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/etc/sudoers.d) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283351.3870976,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769283350.4924953,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /etc/sudoers.d/99-charonte-dexmachina || test -L /etc/sudoers.d/99-charonte-dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /etc/sudoers.d/99-charonte-dexmachina || ls -ld /etc/sudoers.d/99-charonte-dexmachina )'"
                },
                {
                    "timestamp": 1769283350.9429545,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /etc/sudoers.d || test -L /etc/sudoers.d ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /etc/sudoers.d 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /etc/sudoers.d || ls -ld /etc/sudoers.d )'"
                },
                {
                    "timestamp": 1769283351.3872619,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'test -e /etc/sudoers.d/99-charonte-dexmachina && ( sha1sum /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || shasum /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || sha1 /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null ) || true'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769283350.4923735,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283350.4924953,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /etc/sudoers.d/99-charonte-dexmachina || test -L /etc/sudoers.d/99-charonte-dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /etc/sudoers.d/99-charonte-dexmachina || ls -ld /etc/sudoers.d/99-charonte-dexmachina )'"
                },
                {
                    "timestamp": 1769283350.9428334,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/etc/sudoers.d) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283350.9429545,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /etc/sudoers.d || test -L /etc/sudoers.d ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /etc/sudoers.d 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /etc/sudoers.d || ls -ld /etc/sudoers.d )'"
                },
                {
                    "timestamp": 1769283351.3870976,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/etc/sudoers.d/99-charonte-dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283351.3872619,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'test -e /etc/sudoers.d/99-charonte-dexmachina && ( sha1sum /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || shasum /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null || sha1 /etc/sudoers.d/99-charonte-dexmachina 2> /dev/null ) || true'"
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
            "operation": "Validate sudo rule 99-charonte-dexmachina",
            "changed": true,
            "success": true,
            "retry_count": 0,
            "duration": 0.4152531623840332,
            "facts_collected": [],
            "operation_commands": [
                {
                    "timestamp": 1769283351.7668397,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'visudo -c -f /etc/sudoers.d/99-charonte-dexmachina'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769283351.7668397,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'visudo -c -f /etc/sudoers.d/99-charonte-dexmachina'"
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
            "operation": "server.group",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 0.8032639026641846,
            "facts_collected": [
                {
                    "timestamp": 1769283352.1825817,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Groups () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283352.5135427,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Os () (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769283352.1826324,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
                },
                {
                    "timestamp": 1769283352.5135996,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769283352.1825817,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Groups () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283352.1826324,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
                },
                {
                    "timestamp": 1769283352.5135427,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Os () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283352.5135996,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
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
            "operation": "server.group",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 0.7676396369934082,
            "facts_collected": [
                {
                    "timestamp": 1769283352.9860904,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Groups () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283353.3531942,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Os () (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769283352.9861417,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
                },
                {
                    "timestamp": 1769283353.3532543,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769283352.9860904,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Groups () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283352.9861417,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
                },
                {
                    "timestamp": 1769283353.3531942,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Os () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283353.3532543,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
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
            "operation": "server.user",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 1.6048448085784912,
            "facts_collected": [
                {
                    "timestamp": 1769283353.7540016,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Users () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283354.3315556,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Groups () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283354.741862,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Os () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283355.10591,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769283353.7540562,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'for i in `cat /etc/passwd | cut -d: -f1`; do\n            ENTRY=`grep ^$i: /etc/passwd`;\n            LASTLOG=`(((lastlog -u $i || lastlogin $i) 2> /dev/null) | grep ^$i | tr -s '\"'\"' '\"'\"')`;\n            PASSWORD=`(grep ^$i: /etc/shadow || grep ^$i: /etc/master.passwd) 2> /dev/null | cut -d: -f2`;\n            echo \"$ENTRY|`id -gn $i`|`id -Gn $i`|$LASTLOG|$PASSWORD\";\n        done'"
                },
                {
                    "timestamp": 1769283354.3316107,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
                },
                {
                    "timestamp": 1769283354.7419145,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
                },
                {
                    "timestamp": 1769283355.1060386,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769283353.7540016,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Users () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283353.7540562,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'for i in `cat /etc/passwd | cut -d: -f1`; do\n            ENTRY=`grep ^$i: /etc/passwd`;\n            LASTLOG=`(((lastlog -u $i || lastlogin $i) 2> /dev/null) | grep ^$i | tr -s '\"'\"' '\"'\"')`;\n            PASSWORD=`(grep ^$i: /etc/shadow || grep ^$i: /etc/master.passwd) 2> /dev/null | cut -d: -f2`;\n            echo \"$ENTRY|`id -gn $i`|`id -Gn $i`|$LASTLOG|$PASSWORD\";\n        done'"
                },
                {
                    "timestamp": 1769283354.3315556,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Groups () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283354.3316107,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'cat /etc/group'"
                },
                {
                    "timestamp": 1769283354.741862,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "server.Os () (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283354.7419145,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c 'uname -s'"
                },
                {
                    "timestamp": 1769283355.10591,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769283355.1060386,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-vAWcg6yD1B70 *** sudo -H -A -k sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
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
        "Ensure sudo rule 99-charonte-dexmachina": {
            "count": 1,
            "total_duration": 1.2744,
            "average_duration": 1.2744,
            "p50_duration": 1.2744,
            "p90_duration": 1.2744,
            "p95_duration": 1.2744,
            "p99_duration": 1.2744
        },
        "Validate sudo rule 99-charonte-dexmachina": {
            "count": 1,
            "total_duration": 0.4153,
            "average_duration": 0.4153,
            "p50_duration": 0.4153,
            "p90_duration": 0.4153,
            "p95_duration": 0.4153,
            "p99_duration": 0.4153
        },
        "server.group": {
            "count": 2,
            "total_duration": 1.5709,
            "average_duration": 0.7854,
            "p50_duration": 0.7854,
            "p90_duration": 0.7997,
            "p95_duration": 0.8015,
            "p99_duration": 0.8029
        },
        "server.user": {
            "count": 1,
            "total_duration": 1.6048,
            "average_duration": 1.6048,
            "p50_duration": 1.6048,
            "p90_duration": 1.6048,
            "p95_duration": 1.6048,
            "p99_duration": 1.6048
        }
    }
}
```
