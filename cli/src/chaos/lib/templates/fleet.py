fleet = {
    "fleet": {
        "restrictions": {
            "allow_list": {
                "host1": {"role_tag1": True},
                "ATTENTION": "host1 is allowed only in role_tag1",
            },
            "black_list": {
                "host2": {},
                "host3": {"role_tag1": True, "role_tag2": False},
                "ATTENTION": "since host2 does not have any role tags, it is blacklisted in all by default",
                "ATTENTION2": "host3 is blacklisted only in role_tag1, but not in role_tag2",
            },
        },
        "boats": [
            {
                "provider": "provider1",
                "config": {"param1": "value1", "param2": "value2"},
            },
            {
                "provider": "provider2",
                "config": {"param1": "value1", "param2": "value2"},
            },
        ],
        "parallelism": 0,
        "hosts": [
            {
                "host1": {"param1": "value1", "param2": "value2"},
                "host2": {"param1": "value1", "param2": "value2"},
            }
        ],
    },
    "ATTENTION": """
All fleet features are completely optional. Boats and hosts are independent of each other.
""",
}
