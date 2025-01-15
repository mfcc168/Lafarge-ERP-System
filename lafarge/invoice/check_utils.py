def prefix_check(name):
    keywords = ["ltd", "dispensary", "limited", "dr",
                "centre", "center", "clinic", "office",
                "warehouse", "medic", "pharm", "hospital", "store"]

    if any(keyword in name for keyword in keywords):
        return True
    return False
