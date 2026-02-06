"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-12-25 10:27:35
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-12-25 10:28:28
FilePath: /align_to_attribute/src/utils/string_operate/string_list_match.py
Description: 取两个字符串列表中的匹配项
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""
from typing import Union

def get_intersection(list_a: Union[list, set], list_b: Union[list, set]) -> list:
    """Return the intersection of two lists."""
    set_a = set(list_a)
    set_b = set(list_b)
    intersection = set_a.intersection(set_b)
    return list(intersection)