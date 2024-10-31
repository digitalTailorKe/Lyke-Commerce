from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # Check if dictionary is actually a dictionary to prevent errors
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    # Return None or a default value if dictionary is not a dict
    return None
