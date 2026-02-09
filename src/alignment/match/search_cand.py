import copy
from collections import defaultdict
from typing import Any, Dict, List

from utils.celery_task import get_completion_result_batch
from utils.vector.query_builders import (
    BoolQueryBuilder,
    TermsQueryBuilder,
)
from utils.vector.RRF import RRF, RRF_Match_Retriever, RRF_Vector_Retriever

from .save import save_result


def parse_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """解析 ES 搜索结果"""
    return [
        {
            "id": hit.get("_id"),
            "profile": hit.get("_source", {}).get("content", ""),
        }
        for hit in results
    ]


def search_by_ioc(results_dict, attribute_dict, es_manager, top_k=10) -> Dict:
    id_iocs_cand = {}
    for entity_id in results_dict:
        entity = attribute_dict.get_value(str(entity_id))
        ioc_list = entity.get("no_semantic_neighbors", [])
        entity_type = entity.get("entity_type", "")

        bool_builder = BoolQueryBuilder()
        has_condition = False
        if ioc_list:
            bool_builder.add_must(TermsQueryBuilder(field="related_ioc", values=ioc_list))
            has_condition = True

        if has_condition:
            query = bool_builder.get_query()
            results = es_manager.perform_search(query, top_k=top_k)
            for i in results[:]:
                if i["_source"]["entity_type"] != entity_type:
                    results.remove(i)
            id_iocs_cand[entity_id] = parse_results(results)

    return id_iocs_cand


def search_by_profile(
    results_dict,
    attribute_dict,
    source_vectors,
    es_manager,
    profile_name,
    is_hybrid_mode,
    top_k=10,
) -> Dict:
    id_profile_cand = {}
    for entity_id in results_dict:
        entity = attribute_dict.get_value(str(entity_id))
        profile = results_dict[entity_id].get(profile_name, "")
        entity_type = entity.get("entity_type", "")

        retrievers = [
            RRF_Match_Retriever(item_name="entity_type", content=entity_type),
            RRF_Vector_Retriever(vector_field=f"vector_{profile_name}", query_vector=source_vectors[entity_id]),
        ]

        if is_hybrid_mode:
            retrievers.insert(0, RRF_Match_Retriever(item_name="content", content=profile))

        rrf = RRF().add_retrievers(retrievers)
        query = rrf.get_query()

        if "retriever" in query and "rrf" in query["retriever"]:
            query["retriever"]["rrf"]["rank_window_size"] = max(top_k, 50)

        results = es_manager.perform_search(query.copy(), top_k=top_k)

        # 计算 ground_truth 排位
        # 如果排位在前top_k，说明 profile 被用于后续生成
        gt_ids = results_dict[entity_id].get("groud_truth", "")
        rank = -1
        results_dict[entity_id]["ground_truth_rank"] = {}
        for gt_id in gt_ids:
            if gt_id:
                # 检查是否在前top_k名中
                for idx, hit in enumerate(results):
                    if hit["_id"] == str(gt_id):
                        rank = idx + 1
                        break

                # 如果未在前10名中找到，扩大搜索范围查找排位
                if rank == -1:
                    deep_query = query.copy()
                    if "size" in deep_query:
                        del deep_query["size"]
                    deep_query["_source"] = False  # 不需要内容，只需ID计算排位

                    # RRF 要求 rank_window_size >= size
                    if "retriever" in deep_query and "rrf" in deep_query["retriever"]:
                        deep_query["retriever"]["rrf"]["rank_window_size"] = 10000

                    # 假设库的大小不会超过 10000，或者只需要关心前 10000 的排名
                    deep_results = es_manager.perform_search(deep_query, top_k=10000)
                    for idx, hit in enumerate(deep_results):
                        if hit["_id"] == str(gt_id):
                            rank = idx + 1
                            break

            results_dict[entity_id]["ground_truth_rank"][str(gt_id)] = rank

            id_profile_cand[entity_id] = parse_results(results)
    return id_profile_cand


def make_content(idx, cand_dict, attribute_dict, name_to_id) -> List[Dict[str, str]]:
    candidates = cand_dict.get(idx, [])
    content = []
    for cand in candidates:
        cand_id = cand["id"]
        # 获取候选实体的名称作为 key
        name = attribute_dict.get_value(str(cand_id)).get("name", "")
        content.append({name: cand["profile"]})
        name_to_id[name].add(cand_id)
    return content


def search_candidates(
    results_dict,
    source_attribute_dict,
    target_attribute_dict,
    source_vectors,
    es_manager,
    profile_name,
    is_ioc_mode,
    is_hybrid_mode,
    direct_prompt_path,
    results_path,
    top_k=10,
):
    ioc_cand_dict = {}
    if is_ioc_mode:
        ioc_cand_dict = search_by_ioc(results_dict, source_attribute_dict, es_manager, top_k=top_k)

    profile_cand_dict = search_by_profile(
        results_dict,
        source_attribute_dict,
        source_vectors,
        es_manager,
        profile_name,
        is_hybrid_mode,
        top_k=top_k,
    )

    ids = []
    contents = []
    name_to_id = defaultdict(set)
    for entity_id in results_dict:
        entity = results_dict.get(entity_id)
        ioc_content = []
        if is_ioc_mode:
            ioc_content = make_content(entity_id, ioc_cand_dict, target_attribute_dict, name_to_id)

        profile_content = make_content(entity_id, profile_cand_dict, target_attribute_dict, name_to_id)

        self_info = {
            "name": entity.get("name", ""),
            "entity_type": entity.get("entity_type", ""),
            "profile": entity.get(profile_name, ""),
        }
        content = {
            "self_info": self_info,
            "ioc_candidates": ioc_content,
            "profile_candidates": profile_content,
        }
        ids.append(entity_id)
        contents.append(content)

    results = get_completion_result_batch(contents, str(direct_prompt_path))

    save_result(ids, results, results_dict, name_to_id, results_path)
