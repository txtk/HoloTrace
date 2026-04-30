import random

import loguru


def get_random_element(input_list):
    if not input_list:
        loguru.error("输入列表为空")
    return random.choice(input_list)


def get_random_key(dictionary):
    """Randomly get a key from a dictionary"""
    if not dictionary:
        raise ValueError("字典不能为空")
    return random.choice(list(dictionary.keys()))


def get_random_model(model_set: dict, max_value):
    """Get the model based on rpd size"""
    value = random.randint(0, max_value)
    # value = random.randint(89, 140)
    value = [k for k, v in model_set.items() if k >= value][0]
    return model_set[value]
