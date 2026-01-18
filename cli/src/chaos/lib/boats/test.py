from omegaconf import OmegaConf
from chaos.lib.boats.paperBoat import PaperBoat

initial_state = OmegaConf.create({
    "fleet": {
        "parallelism": 2,
        "hosts": [
            {"localhost": {"ssh_user": "dex", "ssh_key": "~/.ssh/id_rsa"}},
        ]
    }
})

boat_config = OmegaConf.create({
    "count": 3,
    "base_ip": "10.0.0"
})

try:
    my_boat = PaperBoat(config=boat_config)

    print("--- Old State ---")
    print(OmegaConf.to_yaml(initial_state))

    new_state = my_boat.get_fleet(old_state=initial_state)

    print("\n--- New State (Merged) ---")
    print(OmegaConf.to_yaml(new_state))

except Exception as e:
    print(f"Error: {e}")
