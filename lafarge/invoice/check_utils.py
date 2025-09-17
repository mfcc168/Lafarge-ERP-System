"""
Utility functions for validating customer names and business prefixes.

Provides functionality to check if customer names contain medical or
business-related prefixes that affect document formatting.
"""

from .models import Forbidden_Word


def prefix_check(name):
    """
    Check if a name contains medical/business prefixes or forbidden words.
    
    Args:
        name (str): The name to check
        
    Returns:
        bool: True if name contains prefixes/forbidden words, False otherwise
    """
    keywords = ["ltd", "dispensary", "limited", "dr",
                "centre", "center", "clinic", "office",
                "warehouse", "medic", "pharmacy", "hospital", "store", "medical", "practice"]

    name_lower = name.lower()
    name_words = name_lower.split()
    
    forbidden_words = Forbidden_Word.objects.values_list('word', flat=True)
    forbidden_words_lower = [word.lower() for word in forbidden_words]
    
    if any(keyword in name_words for keyword in keywords) or any(word in name_words for word in forbidden_words_lower):
        return True
    return False
