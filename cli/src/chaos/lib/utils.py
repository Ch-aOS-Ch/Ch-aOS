import shutil
"""This just checks if a SHELL COMMAND exists in the system PATH."""
def checkDep(bin):
    path = shutil.which(bin)
    if path is None:
        return False
    return True
