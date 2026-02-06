"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-07-01 03:55:11
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-07-07 08:09:42
FilePath: /llm-use/src/utils/random.py
Description: 随机工具库
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

import random

import loguru


def get_random_element(input_list):
    if not input_list:
        loguru.error("输入列表为空")
    return random.choice(input_list)


def get_random_key(dictionary):
    """随机获取字典中的一个键"""
    if not dictionary:
        raise ValueError("字典不能为空")
    return random.choice(list(dictionary.keys()))


def get_random_model(model_set: dict, max_value):
    """根据rpd大小获取模型"""
    value = random.randint(0, max_value)
    # value = random.randint(89, 140)
    value = [k for k, v in model_set.items() if k >= value][0]
    return model_set[value]
