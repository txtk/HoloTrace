import os

from alignment.make_adj import find_directed_links
from utils.celery_task import get_completion_result_batch
from config import settings
from utils.file.json_utils import JsonUtils
from utils.vector.get_vector import load_vector_pkl

from .get_neighbours_mes import get_neighbours_mes_dict
from config import ignore_dict
from .self_info import filter_self_info
from .retriver import retriver_standard, retriver_name
from loguru import logger

def find_neighbours(entity, outgoing, incoming, entities, attribute_dict: JsonUtils):
    start_triplets = []
    end_triplets = []
    entity = int(entity)
    if entity in list(entities):
        out_links = outgoing.get(entity, [])
        for i in out_links:
            start_triplet = {
                "start": attribute_dict.get_value(str(entity)),
                "relation": i[0],
                "end": attribute_dict.get_value(str(i[1])),
            }
            start_triplets.append(start_triplet)
        in_links = incoming.get(entity, [])
        for i in in_links:
            end_triplet = {
                "start": attribute_dict.get_value(str(i[1])),
                "relation": i[0],
                "end": attribute_dict.get_value(str(entity)),
            }
            end_triplets.append(end_triplet)
    return start_triplets, end_triplets


def prepare_data(
    ignore_list,
    entity,
    outgoing,
    incoming,
    entities,
    attribute_dict,
    vectors,
    last_items,
    rag_malware, 
    rag_attck, 
    rag_group,
    top_n,
    is_profile: bool,
    is_enhance_mes: bool,
    is_retriver: bool,
    is_hsage: bool,
    profile_name: str,
):
    start_triplets, end_triplets = find_neighbours(entity, outgoing, incoming, entities, attribute_dict)
    entity = attribute_dict.get_value(str(entity))
    last_items_sub = last_items[ : last_items.index(entity.get("entity_type")) + 1]
    # 获取周边邻居信息
    neighbours_mes_dict, has_sub = get_neighbours_mes_dict(
        start_triplets, end_triplets, last_items_sub, top_n, is_profile=is_profile, is_hsage=is_hsage, profile_name=profile_name
    )
    neighbours_mes_list = []
    for k, v in neighbours_mes_dict.items():
        neighbours_mes_list.append(f"{k}: {str(v)}")

    # 筛选实体自身信息
    entity_mes_dict = filter_self_info(entity, is_enhance_mes, ignore_list)
    retriver_list = []
    # 检索得到信息
    if is_retriver:
        similar_entities = retriver_standard(neighbours_mes_dict, entity, rag_malware, rag_attck, rag_group)
        related_texts = retriver_name(entity, vectors, rag_malware, rag_attck, rag_group)
        retriver_list = similar_entities + related_texts
    
    if len(retriver_list) == 0:
        is_retriver = False

    content = {
        "entity_message": str(entity_mes_dict),
        "has_neighbour": has_sub,
        "neighbours": neighbours_mes_list,
        "has_retriver": is_retriver,
        "retrive_info": retriver_list,

    }
    return content, entity


def check_profile(entity, attribute_dict, profile_name):
    entity = attribute_dict.get_value(str(entity))
    if profile_name in entity:
        return True
    return False


def get_profile(
    suffix,
    id_dict,
    attribute_dict,
    outgoing,
    incoming,
    entities,
    vectors,
    last_items,
    rag_malware, 
    rag_attck, 
    rag_group,
    top_n,
    recreate,
    is_profile: bool,
    is_enhance_mes: bool,
    is_retriver: bool,
    is_hsage,
    profile_name: str,
):
    ids_dict = {}
    ignore_list = ignore_dict.get(suffix, [])
    if suffix == "aadm":
        ids_dict["layer3"] = id_dict.get_value("attack-pattern")
        ids_dict["layer4"] = id_dict.get_value("malware")
        ids_dict["layer5"] = id_dict.get_value("intrusion-set")
    else:
        ids_dict["layer3"] = id_dict.get_value("attack-pattern")
        ids_dict["layer4"] = id_dict.get_value("malware")
        ids_dict["layer5"] = id_dict.get_value("intrusion-set")

    for layer, ids in ids_dict.items():
        contents = []
        entity_list = []
        entity_gids = []
        profile_prompt_path = os.path.join(settings.prompt_dir, "profile", f"{layer}.poml")
        for entity_id in ids:
            if check_profile(entity_id, attribute_dict, profile_name) and not recreate:
                continue
            entity_gids.append(entity_id)
            # 生成摘要
            content, entity = prepare_data(
                ignore_list,
                entity_id,
                outgoing,
                incoming,
                entities,
                attribute_dict,
                vectors,
                last_items,
                rag_malware, 
                rag_attck, 
                rag_group,
                top_n,
                is_profile,
                is_enhance_mes,
                is_retriver,
                is_hsage,
                profile_name,
            )
            entity_list.append(entity)
            contents.append(content)

        results = get_completion_result_batch(contents, str(profile_prompt_path))
        for i in range(len(entity_list)):
            profile = results[i]
            entity = entity_list[i]
            entity[profile_name] = profile
            attribute_dict.set_value(str(entity_gids[i]), entity)
        attribute_dict.save_json()
    return attribute_dict


def profile(
    suffix,
    target_tuple_path,
    source_tuple_path,
    target_attribute_path,
    source_attribute_path,
    target_id_dict_path,
    source_id_dict_path,
    target_vector_path,
    source_vector_path,
    last_items,
    rag_malware, 
    rag_attck, 
    rag_group,
    top_n,
    recreate=False,
    is_profile=True,
    is_enhance_mes=False,
    is_retriver=True,
    is_hsage=True,
    profile_name="profile",
):
    target_attribute_dict = JsonUtils(target_attribute_path)
    source_attribute_dict = JsonUtils(source_attribute_path)
    target_id_dict = JsonUtils(target_id_dict_path)
    source_id_dict = JsonUtils(source_id_dict_path)
    target_outgoing, target_incoming, target_entities = find_directed_links(target_tuple_path)
    source_outgoing, source_incoming, source_entities = find_directed_links(source_tuple_path)
    target_vector = load_vector_pkl(target_vector_path)
    source_vector = load_vector_pkl(source_vector_path)

    source_attribute_dict = get_profile(
        suffix,
        source_id_dict,
        source_attribute_dict,
        source_outgoing,
        source_incoming,
        source_entities,
        source_vector,
        last_items,
        rag_malware, 
        rag_attck, 
        rag_group,
        top_n,
        recreate,
        is_profile,
        is_enhance_mes,
        is_retriver,
        is_hsage,
        profile_name,
    )
    logger.info(f"完成源图谱 {suffix} 的 profile 生成")
    source_attribute_dict.save_json(file_path=source_attribute_path)

    target_attribute_dict = get_profile(
        suffix,
        target_id_dict,
        target_attribute_dict,
        target_outgoing,
        target_incoming,
        target_entities,
        target_vector,
        last_items,
        rag_malware, 
        rag_attck, 
        rag_group,
        top_n,
        recreate,
        is_profile,
        is_enhance_mes,
        is_retriver,
        is_hsage,
        profile_name,
    )
    logger.info(f"完成目标图谱 {suffix} 的 profile 生成")

    target_attribute_dict.save_json(file_path=target_attribute_path)
    
