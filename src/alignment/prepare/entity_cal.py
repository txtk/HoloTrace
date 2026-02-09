import math
import re
import zlib
from os import path

import numpy as np
import textstat
from elasticsearch.helpers import scan

from alignment.profile.get_profile import find_neighbours
from config import elastic, settings
from utils.file.json_utils import JsonUtils

pattern = re.compile(r"[. _]")
textstat.set_lang("en_US")

# 获取知识库的唯一实体数量
def get_kb_counts(indices):
    unique_nums = []
    for index in indices:
        # 获取唯一实体总数
        unique_names = set()
        # 这里的 field 可以根据索引不同做调整，但在你的 mapping 中似乎统一用的 'name'
        # rag_attck 中也有 'id'，我们可以优先用 'id' 或者 combined

        query = {"query": {"match_all": {}}, "_source": ["name", "id"]}

        # 使用 scan 批量获取
        for doc in scan(elastic, index=index, query=query):
            source = doc.get("_source", {})
            name = source.get("name")
            entity_id = source.get("id")

            # 对于 attck，优先使用 id 标识唯一性，如果没有则用 name
            if index == "rag_attck":
                identifier = entity_id or name
            else:
                identifier = name

            if identifier:
                unique_names.add(str(identifier).lower().strip())
        unique_nums.append(len(unique_names))
    return unique_nums


def get_layer_records(layer_json, entity_id_dict):
    for layer in list(layer_json.get_keys())[:-1]:
        for item in layer_json.get_value(layer):
            if item in entity_id_dict:
                yield layer, item, entity_id_dict[item]


def calculate_layer_nums(suffix, entity_id_dict, neo4j_type):
    layer_path = path.join(settings.json_dir, f"layer_{suffix}.json")
    layer_json = JsonUtils(layer_path)
    neo4j_static_dict = JsonUtils(path.join(settings.json_dir, f"neo4j_static_{suffix}.json"))
    layer_num_dict = {}
    item_layer_dict = {}

    for layer, item, records in get_layer_records(layer_json, entity_id_dict):
        if layer not in layer_num_dict:
            layer_num_dict[layer] = 0
        layer_num_dict[layer] += len(records)
        item_layer_dict[item] = layer
    neo4j_static_dict.set_value(neo4j_type, layer_num_dict)
    neo4j_static_dict.update(neo4j_type, item_layer_dict)
    neo4j_static_dict.save_json()


def entity_layer_num(start, end, target_id, neo4j_static_dict, target_layer, neo4j_type):
    neo4j_static_dict = neo4j_static_dict.get_value(neo4j_type)
    if start["unique_id"] == target_id:
        related_entity = end
    else:
        related_entity = start

    if related_entity.get("semantic") == 0:
        return None, 0
    related_entity_layer = neo4j_static_dict.get(related_entity["entity_type"])
    if int(related_entity_layer[-1]) > int(target_layer[-1]):
        return "up", 1
    elif int(related_entity_layer[-1]) < int(target_layer[-1]):
        return "down", related_entity.get("hsage")
    else:
        return "down", 1


def count_node_up_and_down(triplets, entity, neo4j_static_dict, layer, neo4j_type):
    """
    统计一个实体在知识图谱中的上层和下层连接节点数量

    Args:
        triplets (list): 三元组列表，每个三元组包含start和end节点
        entity (dict): 目标实体，包含unique_id等属性
        neo4j_static_dict (JsonDataset): Neo4j静态数据字典，用于获取实体层级信息
        layer (str): 目标实体所在的层级

    Returns:
        tuple: (up_num, down_num) 上层连接数和下层连接数
    """
    target_id = entity["unique_id"]
    up_num = 0
    down_num = 0
    for triplet in triplets:
        start = triplet["start"]
        end = triplet["end"]
        layer_type, result = entity_layer_num(start, end, target_id, neo4j_static_dict, layer, neo4j_type)
        if layer_type is None:
            continue
        elif layer_type == "up":
            up_num += result
        elif layer_type == "down":
            down_num += result
    return up_num, down_num


def count_up_total(layer, neo4j_static_dict, neo4j_type):
    layer_list = neo4j_static_dict.get_value("layer_list")
    up_layer_list = layer_list[layer_list.index(layer) + 1 :]

    up_total = 0
    for up_layer in up_layer_list:
        up_total += neo4j_static_dict.get_value(neo4j_type).get(up_layer, 0)
    return up_total

def count_down_total(layer, neo4j_static_dict, neo4j_type):
    layer_list = neo4j_static_dict.get_value("layer_list")
    down_layer_list = layer_list[:layer_list.index(layer)]

    down_total = neo4j_static_dict.get_value(neo4j_type).get(layer, 0)
    for down_layer in down_layer_list:
        down_total += neo4j_static_dict.get_value(neo4j_type).get(down_layer, 0)
    return down_total


# 如果没有上层节点，则整体为0
def get_discrimination(up_num: int, up_total: int):
    if up_num == 0:
        return 0
    return math.log((up_total) / (up_num) + 1) + 1

# 如果没有下层节点，则下层节点贡献为1
def get_corroboration_tesc(down_value: float, down_total: float):
    if down_value == 0:
        return 1
    return math.log(down_value / down_total + 1) + 1

# 获取知识图谱权重
def get_tesc(up_num, up_total, down_value, down_total):
    d = get_discrimination(up_num, up_total)
    i = get_corroboration_tesc(down_value, down_total)
    return d * i


# 获取知识库权重
def get_pkc(entity, malware_total, attck_total, group_total):
    d = 0
    i = 0
    entity_type = entity.get("entity_type", "")
    malware_num = len(entity.get("uncertain_related_malwares", []))
    attack_num = len(entity.get("uncertain_related_attcks", []))
    group_num = len(entity.get("uncertain_related_groups", []))
    if entity_type == "AttackPattern" or entity_type == "attack-pattern":
        d = get_discrimination(0.3 * malware_num + 0.7 * group_num, 0.3 * malware_total + 0.7 * group_total)
        i = get_corroboration_tesc(0, 0)
    elif entity_type == "Malware" or entity_type == "malware":
        d = get_discrimination(group_num, group_total)
        i = get_corroboration_tesc(attack_num, attck_total)
    elif entity_type == "ThreatActor" or entity_type == "intrusion-set":
        d = get_discrimination(0, 0)
        i = get_corroboration_tesc(0.7 * malware_num + 0.3 * attack_num, 0.7 * malware_total + 0.3 * attck_total)
    return d * i


