from typing import Any

import pulumi
import pulumi_proxmoxve as proxmox
from chaos.lib.isles.isle import Isle


class Chmox(Isle):
    """
    Isle for Proxmox provisioning using Pulumi.

    Provides methods to create and manage Proxmox virtual machines
    """

    isle_name = "chaosmox"
    secrets_needed = ["proxmoxve:apiToken", "proxmoxve:endpoint", "proxmoxve:insecure"]

    def build_resources(self, config: dict[str, Any]) -> None:
        """
        Build the resources for the Proxmox Isle.

        Args:
            config (dict[str, any]): A dictionary containing configuration parameters for the Isle.
        """
        vm_name: str = config.get("vm_name", "chaos-vm")
        target_node = config.get("target_node", "pve")
        template_id = config.get("template_id")

        description = config.get("description", "Provisioned by Ch-aOS Proxmox Isle")

        cores = config.get("cores", 2)
        type_cpu = config.get("type", "x86-64-v2-AES")
        memory = config.get("memory", 2048)
        network_devices = config.get(
            "network_devices", [{"bridge": "vmbr0", "model": "virtio"}]
        )

        ip_configs = config.get("ip_configs", [{"ipv4": {"address": "dhcp"}}])

        ssh_public_key = config.get("ssh_public_key")
        username = config.get("admin_user", "lappis")
        tags = config.get("tags", [])

        clone_full = config.get("clone_full", False)

        disks = config.get(
            "disks", [{"size": 50, "interface": "scsi0", "datastore_id": "local-lvm"}]
        )

        vm = proxmox.VmLegacy(
            vm_name,
            opts=pulumi.ResourceOptions(parent=self),
            name=vm_name,
            node_name=target_node,
            description=description,
            clone={"vm_id": template_id, "full": clone_full} if template_id else None,
            cpu={"cores": cores, "type": type_cpu},
            memory={"dedicated": memory},
            agent={"enabled": True, "trim": True},
            network_devices=network_devices,
            tags=tags,
            disks=disks,
            initialization={
                "ip_configs": ip_configs,
                "user_account": {
                    "username": username,
                    "keys": [ssh_public_key] if ssh_public_key else [],
                },
            },
        )

        pulumi.export(f"{vm_name}_id", vm.id)
        pulumi.export(f"{vm_name}_ipv4_addresses", vm.ipv4_addresses)
