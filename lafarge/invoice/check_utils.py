from .models import Forbidden_Word

def prefix_check(name):
    keywords = ["ltd", "dispensary", "limited", "dr",
                "centre", "center", "clinic", "office",
                "warehouse", "medic", "pharmacy", "hospital", "store", "medical", "practice"]

    if any(keyword in name.split() for keyword in keywords) or any(word in name.split() for word in Forbidden_Word.word):
        return True
    return False
