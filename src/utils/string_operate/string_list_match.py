from typing import Union

def get_intersection(list_a: Union[list, set], list_b: Union[list, set]) -> list:
    """Return the intersection of two lists."""
    set_a = set(list_a)
    set_b = set(list_b)
    intersection = set_a.intersection(set_b)
    return list(intersection)