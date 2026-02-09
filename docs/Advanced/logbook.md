# Ch-aOS Logbook

Ok, you've managed your system beautifully, incredible! But what if something goes wrong? What if you need to uncover why something is not going fast enough, or why a change didn't apply as expected? You don't want to be left to check massive `--verbose` logs, and most certainly not check each host individually. So...

Ch-aOS has a built-in state of the art data collection mechanism called the "Logbook". It was designed to collect the most amount of pure useful data while minimizing the performance impact on the system.

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

"Data collection" has a bad ring to it doesn't it? Well, not in Ch-aOS. All logbooks are stored in a structured json format. Locally. At least out of the box.

You see, when I was developing the logbook system, I quickly realized that storing everything in a single JSON file would not scale well for larger runs. So I had to come up with a better solution.

Then I made a SQLite database backend for the Logbook, which was cool and all, but then I realized that not everyone would want to deal with databases, and that SQLite doesn't really scale well for concurrent access.

So, the final solution was quite simple: plugins (Duh)! Ch-aOS has a plugin system for almost everything, so why not for the Logbook storage as well?

Learn more [here](../Plugins/limani.md).!

They can be found in these places while using the default "chrima" plugin:

- `./chaos-logbook.json`

- `~/.local/share/chaos/logbooks/logbook.db`

Do note that the JSON file is always created, regardless of the storage backend used. It is there for easy access and quick debugging.

## Enabling and disabling:

To enable, run
```bash
chaos apply --logbook --limani <limani_name>
```

Note that you can configure a default limani in your `~/.config/chaos/config.yml` like so:
```yaml
limani: (limani_name)
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
    "run_id": "chaos-2026/01/26-21:29:13",
    "uggly_run_id": "chaos-1769462953-7451800858269",
    "hailer": {
        "user": "dexmachina",
        "boatswain": "[Nah, you're not getting my IP]",
        "hostname": "Dionysus"
    },
    "hosts": {
        "@local": {
            "total_operations": 3,
            "changed_operations": 1,
            "successful_operations": 3,
            "failed_operations": 0,
            "duration": 0.5561,
            "history": [
                {
                    "operation": "Ensuring secrets state directory exists",
                    "changed": false,
                    "success": true,
                    "duration": 0.0997,
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
                    "retry_statistics": {
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
                    "duration": 0.297,
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
                    "retry_statistics": {
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
                    "duration": 0.1594,
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
                    "retry_statistics": {
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
        },
        "Dionysus": {
            "total_operations": 1,
            "changed_operations": 0,
            "successful_operations": 1,
            "failed_operations": 0,
            "duration": 0.035,
            "history": [
                {
                    "operation": "chaos_setup",
                    "changed": false,
                    "success": true,
                    "duration": 0.035,
                    "stdout": "",
                    "stderr": "",
                    "diff": "",
                    "operation_arguments": {
                        "message": "Time spent connecting to hosts and preparing the run."
                    },
                    "retry_statistics": {}
                }
            ]
        }
    },
    "summary": {
        "total_operations": 4,
        "changed_operations": 1,
        "successful_operations": 4,
        "failed_operations": 0,
        "total_duration": 0.5911,
        "status": "in_progress"
    },
    "resource_history": [
        {
            "type": "health_check",
            "host": "@local",
            "stage": "pre_operations",
            "timestamp": 1769462953.6523194,
            "metrics": {
                "cpu_load_1min": 0.67,
                "cpu_load_5min": 0.71,
                "ram_percent": 24.0,
                "ram_used_gb": 3.69,
                "ram_total_gb": 15.37
            }
        },
        {
            "type": "health_check",
            "host": "@local",
            "stage": "post_operations",
            "timestamp": 1769462955.127124,
            "metrics": {
                "cpu_load_1min": 0.67,
                "cpu_load_5min": 0.71,
                "ram_percent": 24.4,
                "ram_used_gb": 3.76,
                "ram_total_gb": 15.37
            }
        }
    ],
    "fact_history": [
        {
            "id": 114,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462953.625242,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "id": 116,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462953.6394317,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.LoadAverage () (ensure_hosts: None)"
        },
        {
            "id": 118,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462953.8033183,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Command (command=cat /var/lib/chaos/secrets.yml || true) (ensure_hosts: None)"
        },
        {
            "id": 121,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462953.9566145,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "id": 123,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.0611074,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "id": 125,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.1574748,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "id": 127,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.2557058,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "id": 129,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.3900864,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.Home (user=dexmachina) (ensure_hosts: None)"
        },
        {
            "id": 131,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.4046955,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "id": 133,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.4293916,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "id": 135,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.4545438,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "id": 137,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.4793203,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "id": 139,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.5030155,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "server.TmpDir () (ensure_hosts: None)"
        },
        {
            "id": 141,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.5272543,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "id": 143,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.6325512,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "id": 145,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.7294667,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
        },
        {
            "id": 147,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.8299549,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
        },
        {
            "id": 149,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.935149,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "id": 151,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.9605896,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
        },
        {
            "id": 153,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462954.985443,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "id": 155,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462955.009414,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
        },
        {
            "id": 160,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462955.1002316,
            "log_level": "DEBUG",
            "context": "fact_gathering",
            "command": "chaos.lib.facts.facts.RamUsage () (ensure_hosts: None)"
        },
        {
            "id": 162,
            "run_id": "chaos-1769462953-7451800858269",
            "timestamp": 1769462955.113255,
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
            "duration": 0.0997,
            "logs": {
                "stdout": "",
                "stderr": ""
            },
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
            "retry_statistics": {
                "retry_attempts": 0,
                "max_retries": 0,
                "retry_info": {
                    "retry_attempts": 0,
                    "max_retries": 0,
                    "was_retried": false,
                    "retry_succeeded": null
                }
            },
            "command_n_fact_history": [
                {
                    "id": 141,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.5272543,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "id": 142,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.5327191,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                }
            ]
        },
        {
            "type": "progress",
            "host": "@local",
            "operation": "Recording new secrets state",
            "changed": false,
            "success": true,
            "duration": 0.297,
            "logs": {
                "stdout": "",
                "stderr": ""
            },
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
            "retry_statistics": {
                "retry_attempts": 0,
                "max_retries": 0,
                "retry_info": {
                    "retry_attempts": 0,
                    "max_retries": 0,
                    "was_retried": false,
                    "retry_succeeded": null
                }
            },
            "command_n_fact_history": [
                {
                    "id": 143,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.6325512,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "id": 144,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.6381323,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos/secrets.yml || test -L /var/lib/chaos/secrets.yml ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos/secrets.yml 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos/secrets.yml || ls -ld /var/lib/chaos/secrets.yml )'"
                },
                {
                    "id": 145,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.7294667,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/var/lib/chaos) (ensure_hosts: None)"
                },
                {
                    "id": 146,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.7347271,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k sh -c '! (test -e /var/lib/chaos || test -L /var/lib/chaos ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /var/lib/chaos 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /var/lib/chaos || ls -ld /var/lib/chaos )'"
                },
                {
                    "id": 147,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.8299549,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/var/lib/chaos/secrets.yml) (ensure_hosts: None)"
                },
                {
                    "id": 148,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.8355799,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k sh -c 'test -e /var/lib/chaos/secrets.yml && ( sha1sum /var/lib/chaos/secrets.yml 2> /dev/null || shasum /var/lib/chaos/secrets.yml 2> /dev/null || sha1 /var/lib/chaos/secrets.yml 2> /dev/null ) || true'"
                }
            ]
        },
        {
            "type": "progress",
            "host": "@local",
            "operation": "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina",
            "changed": true,
            "success": true,
            "duration": 0.1594,
            "logs": {
                "stdout": "",
                "stderr": ""
            },
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
            "retry_statistics": {
                "retry_attempts": 0,
                "max_retries": 0,
                "retry_info": {
                    "retry_attempts": 0,
                    "max_retries": 0,
                    "was_retried": false,
                    "retry_succeeded": null
                }
            },
            "command_n_fact_history": [
                {
                    "id": 149,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.935149,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "id": 150,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.9405642,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina/hi.txt || test -L /home/dexmachina/hi.txt ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina/hi.txt 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina/hi.txt || ls -ld /home/dexmachina/hi.txt )'"
                },
                {
                    "id": 151,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.9605896,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Directory (path=/home/dexmachina) (ensure_hosts: None)"
                },
                {
                    "id": 152,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.9658906,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c '! (test -e /home/dexmachina || test -L /home/dexmachina ) || ( stat -c '\"'\"'user=%U group=%G mode=%A atime=%X mtime=%Y ctime=%Z size=%s %N'\"'\"' /home/dexmachina 2> /dev/null || stat -f '\"'\"'user=%Su group=%Sg mode=%Sp atime=%a mtime=%m ctime=%c size=%z %N%SY'\"'\"' /home/dexmachina || ls -ld /home/dexmachina )'"
                },
                {
                    "id": 153,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.985443,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.Sha1File (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "id": 154,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462954.990778,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c 'test -e /home/dexmachina/hi.txt && ( sha1sum /home/dexmachina/hi.txt 2> /dev/null || shasum /home/dexmachina/hi.txt 2> /dev/null || sha1 /home/dexmachina/hi.txt 2> /dev/null ) || true'"
                },
                {
                    "id": 155,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462955.009414,
                    "log_level": "DEBUG",
                    "context": "fact_gathering",
                    "command": "files.FileContents (path=/home/dexmachina/hi.txt) (ensure_hosts: None)"
                },
                {
                    "id": 156,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462955.0148454,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c 'cat /home/dexmachina/hi.txt'"
                },
                {
                    "id": 157,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462955.0330842,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c 'cp /tmp/tmp028e11k_ /home/dexmachina/hi.txt'"
                },
                {
                    "id": 158,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462955.0502923,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c 'chown dexmachina /home/dexmachina/hi.txt'"
                },
                {
                    "id": 159,
                    "run_id": "chaos-1769462953-7451800858269",
                    "timestamp": 1769462955.066942,
                    "log_level": "DEBUG",
                    "context": "running_command_on_localhost",
                    "command": "env SUDO_ASKPASS=/tmp/pyinfra-sudo-askpass-zX6bBpJA0xbp *** sudo -H -A -k -u dexmachina sh -c 'chmod 600 /home/dexmachina/hi.txt'"
                }
            ]
        },
        {
            "type": "progress",
            "host": "Dionysus",
            "operation": "chaos_setup",
            "changed": false,
            "success": true,
            "duration": 0.035,
            "logs": {},
            "diff": "",
            "operation_arguments": {
                "message": "Time spent connecting to hosts and preparing the run."
            },
            "retry_statistics": {},
            "command_n_fact_history": []
        }
    ],
    "operation_summary": {
        "Ensuring secrets state directory exists": {
            "count": 1,
            "total_duration": 0.0997,
            "average_duration": 0.0997,
            "p50_duration": 0.0997,
            "p90_duration": 0.0997,
            "p95_duration": 0.0997,
            "p99_duration": 0.0997
        },
        "Recording new secrets state": {
            "count": 1,
            "total_duration": 0.297,
            "average_duration": 0.297,
            "p50_duration": 0.297,
            "p90_duration": 0.297,
            "p95_duration": 0.297,
            "p99_duration": 0.297
        },
        "Deploy secret template to /home/dexmachina/hi.txt for user dexmachina": {
            "count": 1,
            "total_duration": 0.1594,
            "average_duration": 0.1594,
            "p50_duration": 0.1594,
            "p90_duration": 0.1594,
            "p95_duration": 0.1594,
            "p99_duration": 0.1594
        },
        "chaos_setup": {
            "count": 1,
            "total_duration": 0.035,
            "average_duration": 0.035,
            "p50_duration": 0.035,
            "p90_duration": 0.035,
            "p95_duration": 0.035,
            "p99_duration": 0.035
        }
    }
}
```
