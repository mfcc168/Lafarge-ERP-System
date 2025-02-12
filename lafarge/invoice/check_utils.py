from .models import Forbidden_Word

def prefix_check(name):
    keywords = ["ltd", "dispensary", "limited", "dr",
                "centre", "center", "clinic", "office",
                "warehouse", "medic", "pharmacy", "hospital", "store", "medical", "practice"]

    forbidden_words = Forbidden_Word.objects.values_list('word', flat=True)
    if name:
        if any(keyword in name.split() for keyword in keywords) or any(word in name.split() for word in forbidden_words):
            return True
    return False
