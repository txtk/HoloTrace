"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-08-10 12:02:44
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-08-10 12:04:51
FilePath: /task_manage/src/models/database/BaseModel.py
Description: 数据库模型基类，提供通用的表名生成逻辑。
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

import re

from peewee_async import AioModel

from config import db


def make_table_name(model_class):
    model_name = model_class.__name__

    # 处理空字符串
    if not model_name:
        raise ValueError("类名不能为空")

    # 将驼峰命名转换为蛇形命名
    # 在大写字母前插入下划线，然后转换为小写
    snake_case = re.sub("([A-Z])", r"_\1", model_name).lower()

    # 移除特殊字符，只保留字母、数字和下划线
    snake_case = re.sub(r"[^a-z0-9_]", "_", snake_case)
    # 处理连续的下划线
    snake_case = re.sub(r"_+", "_", snake_case)
    # 移除开头和结尾的下划线
    snake_case = snake_case.strip("_")

    # 第七步：确保表名不为空
    if not snake_case:
        raise ValueError("无法生成有效的表名")

    return snake_case


class BaseModel(AioModel):
    class Meta:
        database = db
        table_function = make_table_name
