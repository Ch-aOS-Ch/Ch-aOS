from chaos.lib.boats.base import Boat


class PaperBoat(Boat):
    name = "mock"

    def check_connection(self) -> bool:
        """Mock check_connection method for the PaperBoat."""
        return True

    def get_fleet_config(self) -> dict:
        """Mock get_fleet_config method for the PaperBoat."""
        count = self.config.get("count", 1)
        base_ip = self.config.get("base_ip", "192.168.0")

        fake_api_response = {"instances": []}

        for i in range(1, count + 1):
            fake_api_response["instances"].append(
                {
                    "id": f"mock-instance-{i + 1}",
                    "ip_address": f"{base_ip}.{i + 10}",
                    "status": "running",
                    "cpu_load": 0.1 * (i + 1),
                    "tags": {"environment": "testing", "boat_type": "paperBoat"},
                }
            )

        return fake_api_response

    def handle_boat_logic(self, fleet_config: dict) -> dict | list:
        """Mock handle_boat_logic method for the PaperBoat."""
        hosts_payload = []
        for instance in fleet_config.get("instances", []):
            host_info = {
                instance["id"]: {
                    "ip": instance["ip_address"],
                    "status": instance["status"],
                    "cpu_load": instance["cpu_load"],
                    "tags": instance["tags"],
                }
            }
            hosts_payload.append(host_info)

        return hosts_payload
