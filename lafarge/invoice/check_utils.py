def prefix_check(name):
    keywords = ["ltd", "dispensary", "limited"]

    if any(keyword in name for keyword in keywords):
        return True
    return False