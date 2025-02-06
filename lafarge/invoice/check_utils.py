def prefix_check(name):
    keywords = ["ltd", "dispensary", "limited", "dr",
                "centre", "center", "clinic", "office",
                "warehouse", "medic", "pharmacy", "hospital", "store", "medical", "practice"]

    if any(keyword in name.split() for keyword in keywords):
        return True
    return False
