def prefix_check(name):
    keywords = ["ltd", "dispensary", "limited", "dr"]

    if any(keyword in name for keyword in keywords):
        return True
    return False
