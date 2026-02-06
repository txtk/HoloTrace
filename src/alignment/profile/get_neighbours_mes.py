import random


def json_init(input_dict, key, inital_value):
    if key not in input_dict:
        input_dict[key] = inital_value
    return input_dict


def insert_semantic_dict(entity, entity_type, neighbours_mes_dict, last_items, is_profile, profile_name):
    # 如果 semantic 不为 1，则直接返回
    if entity.get("semantic") != 1:
        return neighbours_mes_dict

    if entity_type in last_items:
        # 确保 entity_type 对应的键存在且为列表
        neighbours_mes_dict = json_init(neighbours_mes_dict, entity_type, [])

        if is_profile:
            neighbour_data = {
                "name": entity.get("name"),
                "hsage": entity.get("hsage", 0),
                "profile": entity.get(profile_name, "none"),
                # "profile": entity.get("profile_without_enhance", "none"),
            }
        else:
            # 创建包含 name 和 hsage 的字典
            neighbour_data = {
                "name": entity.get("name"),
                "hsage": entity.get("hsage", 0),
            }

        # 将新创建的字典追加到列表中
        neighbours_mes_dict[entity_type].append(neighbour_data)

    return neighbours_mes_dict


def generate_neighbours_mes_dict(neighbours_mes_dict, triples, mode, last_items, is_profile, profile_name):
    for triple in triples:
        if mode == "start":
            end = triple["end"]
            end_type = end.get("entity_type")
            neighbours_mes_dict = insert_semantic_dict(
                end, end_type, neighbours_mes_dict, last_items, is_profile, profile_name
            )

        else:
            start = triple["start"]
            start_type = start.get("entity_type")
            neighbours_mes_dict = insert_semantic_dict(
                start, start_type, neighbours_mes_dict, last_items, is_profile, profile_name
            )

    return neighbours_mes_dict


def finalize_and_sort_profiles(input_dict, is_hsage, top_n=5):
    """
    对 profile_dict 中的每个实体类型的列表进行处理：
    1. 根据 hsage 的值降序排序。
    2. 只保留前 top_n 个元素。
    3. 提取 "profile" 字段，使列表最终只包含字符串。
    """
    final_dict = {}
    for entity_type, profiles_with_scores in input_dict.items():
        random.shuffle(profiles_with_scores)
        if is_hsage:
            # 1. 使用 lambda 函数根据 hsage 的值进行降序排序
            sorted_profiles = sorted(profiles_with_scores, key=lambda x: x["hsage"], reverse=True)
        else:
            sorted_profiles = profiles_with_scores

        # 2. 保留排序后的前 top_n 个元素
        top_profiles = sorted_profiles[:top_n]
        for d in top_profiles:
            d.pop("hsage", None)
        # 将处理好的列表存入新的字典
        if len(top_profiles) > 0:
            final_dict[entity_type] = top_profiles

    return final_dict


def get_neighbours_mes_dict(
    start_triplets,
    end_triplets,
    last_items,
    top_n=5,
    is_profile: bool = True,
    is_hsage: bool = True,
    profile_name="profile",
):
    neighbours_mes_dict = {}
    neighbours_mes_dict = generate_neighbours_mes_dict(
        neighbours_mes_dict, start_triplets, "start", last_items, is_profile, profile_name
    )
    neighbours_mes_dict = generate_neighbours_mes_dict(
        neighbours_mes_dict, end_triplets, "end", last_items, is_profile, profile_name
    )

    neighbours_mes_dict = finalize_and_sort_profiles(neighbours_mes_dict, is_hsage, top_n)
    if len(neighbours_mes_dict) > 0:
        has_sub = True
    else:
        has_sub = False
    return neighbours_mes_dict, has_sub
