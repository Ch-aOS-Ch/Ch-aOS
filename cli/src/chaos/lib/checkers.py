import sys

def checkRoles(ROLES_DISPATCHER, **kwargs):
    print("Discovered Roles:")
    if not ROLES_DISPATCHER:
        print("No roles found.")
    else:
        for p in ROLES_DISPATCHER:
            print(f"  -{p}")

def checkExplainations(EXPLAINATIONS, **kwargs):
    print("Discovered Explainations:")
    if not EXPLAINATIONS:
        print("No explainations found.")
    else:
        for p in EXPLAINATIONS:
            print(f"  -{p}")

def checkAliases(ROLE_ALIASES, **kwargs):
    print("Discovered Aliases for Roles:")
    if not ROLE_ALIASES:
        print("No aliases found.")
    else:
        for p, r in ROLE_ALIASES.items():
            print(f"\n  -{p} ~> -{r}")
            print("_____________________________________________")
