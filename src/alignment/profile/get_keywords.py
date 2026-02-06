from utils.name_process import get_name



def json_init(input_dict, key, inital_value):
    if key not in input_dict:
        input_dict[key] = inital_value
    return input_dict


def insert_property_dict(entity, entity_type, profile_dict, last_items, property_name="profile"):
    """
    将实体的 profile 和 nf_ipf 值作为一个字典添加到列表中。
    """
    # 如果 semantic 不为 1，则直接返回
    if entity.get(entity_type, {}).get("semantic") != 1:
        return profile_dict

    if entity_type in last_items:
        # 确保 entity_type 对应的键存在且为列表
        profile_dict = json_init(profile_dict, entity_type, [])

        # 创建包含 profile 和 nf_ipf 的字典
        profile_data = {
            property_name: entity[entity_type].get(property_name),
            "nf_ipf": entity[entity_type].get("nfipf", 0) # 使用 .get 避免因缺少 nf_ipf 字段而报错，默认值为0
        }
        
        # 将新创建的字典追加到列表中
        profile_dict[entity_type].append(profile_data)

    return profile_dict

def insert_semantic_dict(entity, entity_type, keyword_dict, last_items):
    # 如果 semantic 不为 1，则直接返回
    if entity.get("semantic") != 1:
        return keyword_dict

    if entity_type in last_items:
        # 确保 entity_type 对应的键存在且为列表
        keyword_dict = json_init(keyword_dict, entity_type, [])

        # 创建包含 profile 和 nf_ipf 的字典
        keyword_data = {
            "keywords": get_name(entity),
            "nf_ipf": entity.get("nf_ipf", 0) # 使用 .get 避免因缺少 nf_ipf 字段而报错，默认值为0
        }
        
        # 将新创建的字典追加到列表中
        keyword_dict[entity_type].append(keyword_data)

    return keyword_dict


def generate_keyword_dict(keyword_dict, triples, mode, last_items):
    for triple in triples:
        if mode == "start":
            end = triple["end"]
            end_type = end.get("entity_type")
            keyword_dict = insert_semantic_dict(end, end_type, keyword_dict, last_items)

        else:
            start = triple["start"]
            start_type = start.get("entity_type")
            keyword_dict = insert_semantic_dict(start, start_type, keyword_dict, last_items)

    return keyword_dict


def finalize_and_sort_profiles(input_dict, key_name, top_n=5):
    """
    对 profile_dict 中的每个实体类型的列表进行处理：
    1. 根据 nf_ipf 的值降序排序。
    2. 只保留前 top_n 个元素。
    3. 提取 "profile" 字段，使列表最终只包含字符串。
    """
    final_dict = {}
    for entity_type, profiles_with_scores in input_dict.items():
        # 1. 使用 lambda 函数根据 nf_ipf 的值进行降序排序
        sorted_profiles = sorted(
            profiles_with_scores, 
            key=lambda x: x['nf_ipf'], 
            reverse=True
        )
        
        # 2. 保留排序后的前 top_n 个元素
        top_profiles = sorted_profiles[:top_n]
        
        # 3. 使用列表推导式提取 "profile" 字符串
        final_profiles_list = [item[key_name] for item in top_profiles]
        
        # 将处理好的列表存入新的字典
        final_dict[entity_type] = final_profiles_list
        
    return final_dict



def get_keyword_dict(start_triplets, end_triplets, last_items, top_n=5):
    keyword_dict = {}
    keyword_dict = generate_keyword_dict(keyword_dict, start_triplets, "start", last_items)
    keyword_dict = generate_keyword_dict(keyword_dict, end_triplets, "end", last_items)

    keyword_dict = finalize_and_sort_profiles(keyword_dict, "keywords", top_n)
    if len(keyword_dict) > 0:
        has_sub = True
    else:
        has_sub = False
    return keyword_dict, has_sub