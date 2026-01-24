# Ch-aOS Logbook

Ch-aOS has a built-in state of the art data collection mechanism called the "Logbook". It was designed to collect the most ammount of pure useful data while minimizing the performance impact on the system.

It is a complete execution journal that captures a precise, structured and replayable record of everything that happened during a `chaos apply` run, from the high-level operations down to the EXACT commands, facts, timestamps, and system state before and after each operation.

When I designed the Logbook, I had one singular goal in mind: collect as many useful data with as little as possible of a performance hit.

To put it to the exact thoughts that ran through my mind when designing it: "**Pull absolutely, undoubtedly, and completely ZERO punches**" when it comes to observability. If a piece of data can be useful on any level, it BELONGS to the Logbook. No compromises.

## What data is collected?

For each execution, the Logbook captures:

- Per-operation metadata and outcomes

- Exact commands executed, with timestamps and execution order

- Fact history and fact changes that influenced decisions

- Retry statistics and execution timings

- Diffs and change detection

- Command outputs (with sensitive data filtered when applicable)

- Host-level metrics (CPU, RAM, health checks)

And even the exact sequence of commands and facts gathered for each operation, both alone and together, in order. This comes from the times where I needed to debug a ansible playbook and it simply wouldn't give me enough info to figure out what was going on. With this level of detail, you can reconstruct the entire execution flow and understand exactly what happened, when, and why.

## No ops? Boohoo, still logged!

Even when no operations are executed (say, when everything is already in the desired state), the Logbook still captures:

- pre and post operation health checks

- exact fact history and timestamps that led to... Well, to no ops being ran

Again, debugging background, "No operations" is still a state that needs to be understood sometimes. The Logbook captures it all.

## Storage and format:

"Data collection" has a bad ring to it doesn't it? Well, not in Ch-aOS. All logbooks are stored in a structured json format. Locally.

They can be found in these places:

- `./chaos-logbook.json`

- `~/.local/share/chaos/logbooks/chaos_logbook_run{run_id}_{timestamp}.json`

Your data is yours, it is never streamed anywhere other than the stdout (in real time btw).

## Enabling and disabling:

To enable, run
```bash
chaos apply --logbook
```

To disable, simply omit the `--logbook` flag. That simple. The logging system is not even enabled on the background.

## Privacy and Ownership:

The Logbook is *local by design*.

NO data is transmitted to any external servers. NO third-party is involved.

If the `--logbook` is omitted, the data collection system doesn't even turn on.

Also, it is Free and Open Source. No ifs or elses or buts about it. Forever.

## Why?

The Logbook is designed for an old me who needed to debug some serious infra issues. It was made to empower YOU to debug your own infra issues.

If you ever needed to figure out why something didn't go as expected, the Logbook is your friend. It gives you the power to reconstruct and analyze every detail of your infrastructure changes.

It was made to be useful for users, not only machines or senior engineers.

### Example:
Here goes a simple Logbook of a singular role being applied to a singular host:

```json
{
    "api_version": "v1",
    "run_id": "chaos-2026/01/24-22:41:15",
    "uggly_run_id": "chaos-1769294475-35764876269780",
    "hailer": {
        "user": "dexmachina",
        "boatswain": "[Nah, you're no getting my IP]",
        "hostname": "Dionysus"
    },
    "hosts": {
        "@local": {
            "total_operations": 3,
            "changed_operations": 1,
            "successful_operations": 3,
            "failed_operations": 0,
            "duration": 1.5996980667114258,
            "history": [
                {
                    "type": "setup_phase",
                    "stage": "connection_and_facts",
                    "timestamp": 1769294478.5274992,
                    "duration": 2.7274,
                    "success": true
                },
                {
                    "operation": "Ensuring secrets state directory exists",
                    "changed": false,
                    "success": true,
                    "duration": 0.284,
                    "stdout": "",
                    "stderr": "",
                    "diff": "",
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
                    "changed": false,
                    "success": true,
                    "duration": 1.2315,
                    "stdout": "",
                    "stderr": "",
                    "diff": "",
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
                    "operation": "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina",
                    "changed": true,
                    "success": true,
                    "duration": 0.0842,
                    "stdout": "",
                    "stderr": "",
                    "diff": "Will modify /home/dexmachina/hi.txt\n  @@ -1 +1 @@\n  - nooooooooo\n[SENSITIVE DATA FILTERED]\n\nSuccess",
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
        "changed_operations": 1,
        "successful_operations": 3,
        "failed_operations": 0,
        "status": "success",
        "total_duration": 1.5996980667114258
    },
    "resource_history": [
        {
            "type": "health_check",
            "host": "@local",
            "stage": "pre_operations",
            "timestamp": 1769294478.5326884,
            "metrics": {
                "cpu_load_1min": 0.63,
                "cpu_load_5min": 0.7,
                "ram_percent": 42.0,
                "ram_used_gb": 6.46,
                "ram_total_gb": 15.37
            }
        },
        {
            "type": "health_check",
            "host": "@local",
            "stage": "post_operations",
            "timestamp": 1769294484.327481,
            "metrics": {
                "cpu_load_1min": 0.66,
                "cpu_load_5min": 0.7,
                "ram_percent": 41.8,
                "ram_used_gb": 6.43,
                "ram_total_gb": 15.37
            }
        }
    ],
    "command_history": [
        {
            "timestamp": 1769294482.7225926,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
        },
        {
            "timestamp": 1769294483.0070384,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
        },
        {
            "timestamp": 1769294483.3427455,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
        },
        {
            "timestamp": 1769294483.7029817,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769294484.2389967,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
        },
        {
            "timestamp": 1769294484.2502532,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
        },
        {
            "timestamp": 1769294484.264085,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
        },
        {
            "timestamp": 1769294484.2741976,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
        },
        {
            "timestamp": 1769294484.286225,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmpjqks7iuv /home/dexmachina/hi.txt'"
        },
        {
            "timestamp": 1769294484.2978399,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
        },
        {
            "timestamp": 1769294484.3105054,
            "log_level": "DEBUG",
            "context": "running_command_on_localhost",
            "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
        }
    ],
    "fact_history": [
        {
            "timestamp": 1769294478.528359,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294478.530887,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294478.6753526,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=cat /var/lib/chaos/secrets.yml || true) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294481.1138546,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294481.4634337,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294481.9300227,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.282992,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.659639,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Home (user=dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.662006,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.6732168,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.6843333,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.7025495,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.7123551,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.TmpDir () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294482.7224584,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294483.00692,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294483.342619,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294483.7028704,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294484.2388754,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294484.2499976,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294484.2639694,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294484.27409,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294484.3233132,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "timestamp": 1769294484.3256319,
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
            "duration": 0.2840418815612793,
            "facts_collected": [
                {
                    "timestamp": 1769294482.7224584,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769294482.7225926,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769294482.7224584,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294482.7225926,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
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
            "duration": 1.2314767837524414,
            "facts_collected": [
                {
                    "timestamp": 1769294483.00692,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294483.342619,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294483.7028704,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769294483.0070384,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
                },
                {
                    "timestamp": 1769294483.3427455,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                },
                {
                    "timestamp": 1769294483.7029817,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769294483.00692,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294483.0070384,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
                },
                {
                    "timestamp": 1769294483.342619,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294483.3427455,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                },
                {
                    "timestamp": 1769294483.7028704,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294483.7029817,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
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
            "duration": 0.08417940139770508,
            "facts_collected": [
                {
                    "timestamp": 1769294484.2388754,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.2499976,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.2639694,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.27409,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                }
            ],
            "operation_commands": [
                {
                    "timestamp": 1769294484.2389967,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
                },
                {
                    "timestamp": 1769294484.2502532,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                },
                {
                    "timestamp": 1769294484.264085,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
                },
                {
                    "timestamp": 1769294484.2741976,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769294484.286225,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmpjqks7iuv /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769294484.2978399,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769294484.3105054,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
                }
            ],
            "command_n_facts_in_order": [
                {
                    "timestamp": 1769294484.2388754,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.2389967,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
                },
                {
                    "timestamp": 1769294484.2499976,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.2502532,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                },
                {
                    "timestamp": 1769294484.2639694,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.264085,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
                },
                {
                    "timestamp": 1769294484.27409,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "timestamp": 1769294484.2741976,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769294484.286225,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmpjqks7iuv /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769294484.2978399,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
                },
                {
                    "timestamp": 1769294484.3105054,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-7XMslrbaHmy1 *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
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
            "total_duration": 0.284,
            "average_duration": 0.284,
            "p50_duration": 0.284,
            "p90_duration": 0.284,
            "p95_duration": 0.284,
            "p99_duration": 0.284
        },
        "Recording new secrets state": {
            "count": 1,
            "total_duration": 1.2315,
            "average_duration": 1.2315,
            "p50_duration": 1.2315,
            "p90_duration": 1.2315,
            "p95_duration": 1.2315,
            "p99_duration": 1.2315
        },
        "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina": {
            "count": 1,
            "total_duration": 0.0842,
            "average_duration": 0.0842,
            "p50_duration": 0.0842,
            "p90_duration": 0.0842,
            "p95_duration": 0.0842,
            "p99_duration": 0.0842
        }
    }
}
```
