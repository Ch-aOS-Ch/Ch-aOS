# Ch-aOS Logbook

Ch-aOS has a built-in state of the art data collection mechanism called the "Logbook". It was designed to collect the most ammount of pure useful data while minimizing the performance impact on the system.

It collects data about each operation performed during a `chaos apply --logbook` execution. It has a "pull absolutely, undoubtedly and completely ZERO punches" philosophy when it comes to data collection. This means that it collects EVERYTHING that could be useful for analysis, debugging, and optimization purposes.

It goes from simple "how much has changed" metrics, to detailed per-operation data including command outputs, execution times, retry statistics, diffs, and uniquelly, even the exact commands and facts, along with their timestamps and sequence of execution that led to the final state of each operation.

All of this data is stored LOCALLY in a structured JSON format, making it easy to parse and analyze using various tools and techniques.

"Oh, but no operations ran on this host, so no data was collected!" - you say? Fear not, Ch-aOS is smart enough to still collect host-level metrics such as CPU load and RAM usage before and after the operations phase, and even the fact history that led to the decision of not running any operations.

All of this is Free and Open Source. Forever. No ifs or elses or buts. FOREVER.

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
            "total_operations": 3,
            "changed_operations": 1,
            "successful_operations": 3,
            "failed_operations": 0,
            "duration": 1.4079294204711914,
            "history": [
                {
                    "type": "setup_phase",
                    "stage": "connection_and_facts",
                    "timestamp": 1769288851.090979,
                    "duration": 2.8256,
                    "success": true
                },
                {
                    "operation": "Ensuring secrets state directory exists",
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
                            "_temp_dir": null,
                            "name": "Ensuring secrets state directory exists",
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
                    "duration": 0.3768,
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
                    },
                    "diff": ""
                },
                {
                    "operation": "Recording new secrets state",
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
                            "_temp_dir": null,
                            "name": "Recording new secrets state",
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": false,
                            "hash": "=9c1c01dc3ac1445a500251fc34a15d3e75a849df"
                        },
                        "parent_op_hash": null
                    },
                    "changed": false,
                    "success": true,
                    "duration": 0.9512,
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
                    },
                    "diff": ""
                },
                {
                    "operation": "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina",
                    "operation_arguments": {
                        "global_arguments": {
                            "_sudo": true,
                            "_sudo_user": "dexmachina",
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
                            "_temp_dir": null,
                            "name": "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina",
                            "_ignore_errors": false,
                            "_continue_on_error": false,
                            "_if": []
                        },
                        "operation_meta": {
                            "executed": false,
                            "maybe_change": true,
                            "hash": "=f4f59e822581d785ba910fbf3f268eca79db8204"
                        },
                        "parent_op_hash": null
                    },
                    "changed": true,
                    "success": true,
                    "duration": 0.0799,
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
                    },
                    "diff": "Will modify /home/dexmachina/hi.txt\n  @@ -1 +1 @@\n  - nooooooooo\n[SENSITIVE DATA FILTERED]\n\nSuccess"
                }
            ]
        }
    },
    "summary": {
        "total_operations": 3,
        "changed_operations": 1,
        "successful_operations": 3,
        "failed_operations": 0,
        "status": "success",
        "total_duration": 1.4079294204711914
    },
    "resource_history": [
        {
            "type": "health_check",
            "host": "@local",
            "stage": "pre_operations",
            "timestamp": 1769288851.0968199,
            "metrics": {
                "cpu_load_1min": 0.68,
                "cpu_load_5min": 0.67,
                "ram_percent": 47.9,
                "ram_used_gb": 7.37,
                "ram_total_gb": 15.37
            }
        },
        {
            "type": "health_check",
            "host": "@local",
            "stage": "post_operations",
            "timestamp": 1769288855.5686376,
            "metrics": {
                "cpu_load_1min": 0.7,
                "cpu_load_5min": 0.68,
                "ram_percent": 48.0,
                "ram_used_gb": 7.37,
                "ram_total_gb": 15.37
            }
        }
    ],
    "command_history": [
        {
            "timestamp": 1769288854.1554756,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
        },
        {
            "timestamp": 1769288854.5327759,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
        },
        {
            "timestamp": 1769288854.800163,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
        },
        {
            "timestamp": 1769288855.1644516,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769288855.484477,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
        },
        {
            "timestamp": 1769288855.4963365,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
        },
        {
            "timestamp": 1769288855.5107565,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769288855.524469,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
        },
        {
            "timestamp": 1769288855.5363626,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmpvyiemkf2 /home/dexmachina/hi.txt'"
        },
        {
            "timestamp": 1769288855.5463538,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
        },
        {
            "timestamp": 1769288855.555044,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
        }
    ],
    "fact_history": [
        {
            "timestamp": 1769288851.0926516,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288851.095104,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288851.2491794,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=cat /var/lib/chaos/secrets.yml || true) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288852.9489954,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288853.2125235,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288853.4926178,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288853.772122,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.091587,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Home (user=dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.0942059,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.1055932,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.1166964,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.1353545,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.145277,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.TmpDir () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.155345,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.5326447,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288854.8000238,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.1643276,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.4843462,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.4961774,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.5105786,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.5243855,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.56445,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769288855.5669143,
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
            "duration": 0.3768434524536133,
            "facts_collected": [
                {
                    "timestamp": 1769288854.155345,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769288854.1554756,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769288854.155345,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288854.1554756,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
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
            },
            "diff": ""
        },
        {
            "type": "progress",
            "host": "@local",
            "operation": "Recording new secrets state",
            "changed": false,
            "success": true,
            "retry_count": 0,
            "duration": 0.9511985778808594,
            "facts_collected": [
                {
                    "timestamp": 1769288854.5326447,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288854.8000238,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.1643276,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769288854.5327759,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
                },
                {
                    "timestamp": 1769288854.800163,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                },
                {
                    "timestamp": 1769288855.1644516,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769288854.5326447,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288854.5327759,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
                },
                {
                    "timestamp": 1769288854.8000238,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288854.800163,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                },
                {
                    "timestamp": 1769288855.1643276,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.1644516,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
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
            },
            "diff": ""
        },
        {
            "type": "progress",
            "host": "@local",
            "operation": "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina",
            "changed": true,
            "success": true,
            "retry_count": 0,
            "duration": 0.07988739013671875,
            "facts_collected": [
                {
                    "timestamp": 1769288855.4843462,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.4961774,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.5105786,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.5243855,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769288855.484477,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
                },
                {
                    "timestamp": 1769288855.4963365,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                },
                {
                    "timestamp": 1769288855.5107565,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
                },
                {
                    "timestamp": 1769288855.524469,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769288855.5363626,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmpvyiemkf2 /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769288855.5463538,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769288855.555044,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769288855.4843462,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.484477,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
                },
                {
                    "timestamp": 1769288855.4961774,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.4963365,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                },
                {
                    "timestamp": 1769288855.5105786,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.5107565,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
                },
                {
                    "timestamp": 1769288855.5243855,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769288855.524469,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769288855.5363626,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmpvyiemkf2 /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769288855.5463538,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769288855.555044,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-qlvMKpM14cAg *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
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
            },
            "diff": "Will modify /home/dexmachina/hi.txt\n  @@ -1 +1 @@\n  - nooooooooo\n[SENSITIVE DATA FILTERED]\n\nSuccess"
        }
    ],
    "operation_summary": {
        "Ensuring secrets state directory exists": {
            "count": 1,
            "total_duration": 0.3768,
            "average_duration": 0.3768,
            "p50_duration": 0.3768,
            "p90_duration": 0.3768,
            "p95_duration": 0.3768,
            "p99_duration": 0.3768
        },
        "Recording new secrets state": {
            "count": 1,
            "total_duration": 0.9512,
            "average_duration": 0.9512,
            "p50_duration": 0.9512,
            "p90_duration": 0.9512,
            "p95_duration": 0.9512,
            "p99_duration": 0.9512
        },
        "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina": {
            "count": 1,
            "total_duration": 0.0799,
            "average_duration": 0.0799,
            "p50_duration": 0.0799,
            "p90_duration": 0.0799,
            "p95_duration": 0.0799,
            "p99_duration": 0.0799
        }
    }
}
```
