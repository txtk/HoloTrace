"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-09-22 21:34:19
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-09-23 15:25:46
FilePath: /entity_alignment/src/entity_alignment/profile_tfidf/prune.py
Description: 对构造的知识图谱进行剪枝，去除冗余关系
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

from os import path

from config import settings
from utils.file.json_utils import JsonUtils
from utils.neo4j_pruner import Neo4jPruner


async def prune(neo4j_type):
    pruner = Neo4jPruner(neo4j_type)
    layer_path = path.join(settings.json_dir, "layer.json")
    layer = JsonUtils(layer_path)

    high_list = layer.get_value("layer3") + layer.get_value("layer4") + [layer.get_value("layer2")[1]]
    low_level = layer.get_value("layer1")
    for low in low_level:
        for high in high_list:
            await pruner.execute_pruning(high, low, "indicator")
