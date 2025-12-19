import shutil
def checkDep(bin):
    path = shutil.which(bin)
    if path is None:
        return False
    return True
