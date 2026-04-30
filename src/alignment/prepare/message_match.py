from utils.celery_task import get_embedding_celery
from utils.vector.vector_manager import ElasticsearchVectorManager

from .query_builder import QueryBuilder


def result_save(value, result):
    if "related_groups" in result:
        value["uncertain_related_groups"] = result["related_groups"]
    if "related_malware" in result:
        value["uncertain_related_malware"] = result["related_malware"]
    if "related_attack_patterns" in result:
        value["uncertain_related_attack_patterns"] = result["related_attack_patterns"]
    if "aliases" in result:
        value["uncertain_aliases"] = result["aliases"]
    if "id" in result:
        value["uncertain_id"] = result["id"]

    value["uncertain_name"] = result.get("name", "")
    value["uncertain_mes"] = result.get("raw_content", "")
    return value


def match_by_dict(query_builder, match_dict, rag_vector_manager: ElasticsearchVectorManager):
    for i in match_dict:
        for k, v in i.items():
            if k == "term":
                query = query_builder.build_term_query(v.get("field"), v.get("value"))
            elif k == "terms":
                query = query_builder.build_terms_query(v.get("field"), v.get("value"))
            elif k == "knn":
                query = query_builder.build_knn_query(
                    vector_field=v.get("field", ""),
                    query_vector=v.get("query_vector", []),
                    priority=False,
                )
            elif k == "match":
                query = query_builder.build_match_query(v.get("field"), v.get("value"))
            # Search and return the first result above the threshold
            hits, _ = rag_vector_manager.perform_search_detailed(query)
            for hit in hits:
                if k == "knn":
                    if hit.get("_score", 0) > 0.94:
                        return hit
                else:
                    if hit.get("_score", 0) > 5:
                        return hit
    return None


def message_match(attribute_dict, rag_malware, rag_attck, rag_group, force=False):
    query_builder = QueryBuilder()

    # 1. Collect all names that need embeddings
    names_to_embed = []
    items_to_process = []
    for _, value in attribute_dict.get_items():
        if value.get("processed") and not force:
            continue
        items_to_process.append(value)
        name = value.get("name", "").lower()
        if name and value.get("vector") is None:
            names_to_embed.append(name)

    # 2. Fetch embeddings in batches
    if names_to_embed:
        unique_names = list(set(names_to_embed))
        embeddings = get_embedding_celery(unique_names)
        name_to_vector = dict(zip(unique_names, embeddings))

        for value in items_to_process:
            name = value.get("name", "").lower()
            if value.get("vector") is None and name in name_to_vector:
                value["vector"] = name_to_vector[name]

    # 3. Run matching logic
    for value in items_to_process:
        if force:
            value.pop("uncertain_related_groups", None)
            value.pop("uncertain_related_malware", None)
            value.pop("uncertain_related_attack_patterns", None)
            value.pop("aliases", None)

        name = value.get("name", "").lower()
        entity_type = value.get("entity_type", "")
        result = None

        vector = value.get("vector")
        if vector is None:
            continue

        if entity_type == "ThreatActor" or entity_type == "intrusion-set":
            match_dict = [
                {"term": {"field": "aliases", "value": name}},
                {"knn": {"field": "name_vector", "query_vector": vector}},
            ]
            result = match_by_dict(query_builder, match_dict, rag_group)
        elif entity_type == "Malware" or entity_type == "malware":
            match_dict = [
                {"match": {"field": "name", "value": name}},
                {"knn": {"field": "name_vector", "query_vector": vector}},
            ]
            result = match_by_dict(query_builder, match_dict, rag_malware)
        elif entity_type == "AttackPattern" or entity_type == "attack-pattern":
            match_dict = [
                {"match": {"field": "name", "value": name}},
                {"match": {"field": "id", "value": name}},
                {"knn": {"field": "name_vector", "query_vector": vector}},
            ]
            result = match_by_dict(query_builder, match_dict, rag_attck)
        if result:
            value = result_save(value, result)
        value["processed"] = True
    attribute_dict.save_json()


def threshold_experiment(attribute_dict, rag_malware, rag_attck, rag_group):
    """
    Find the best KNN matching threshold by analyzing the data.
    1. Use strict text matching (Score > 10) to determine Ground Truth.
    2. Run KNN queries on these samples and record scores for correct and distractor results.
    3. Output statistical suggestions and look for a zero-false-positive threshold.
    """

    query_builder = QueryBuilder()

    stats = {"correct_scores": [], "incorrect_scores": []}

    # Iterate over all attributes to match
    items = list(attribute_dict.get_items())

    # 1. Batch-fetch all vectors that need embeddings
    names_to_embed = []
    for _, value in items:
        name = value.get("name", "").lower()
        if name and value.get("vector") is None:
            names_to_embed.append(name)

    if names_to_embed:
        unique_names = list(set(names_to_embed))
        embeddings = get_embedding_celery(unique_names)
        name_to_vector = dict(zip(unique_names, embeddings))
        for _, value in items:
            name = value.get("name", "").lower()
            if value.get("vector") is None and name in name_to_vector:
                value["vector"] = name_to_vector[name]

    for _, value in items:
        name = value.get("name", "").lower()
        entity_type = value.get("entity_type", "")
        if not name or not entity_type:
            continue

        # Get vectors
        vector = value.get("vector")
        if vector is None:
            continue

        # Select the corresponding RAG manager and strict matching strategy
        rag_manager = None
        strict_query = None

        if entity_type in ["ThreatActor", "intrusion-set"]:
            rag_manager = rag_group
            strict_query = query_builder.build_match_query("name", name, priority=False)
        elif entity_type in ["Malware", "malware"]:
            rag_manager = rag_malware
            strict_query = query_builder.build_match_query("name", name, priority=False)
        elif entity_type in ["AttackPattern", "attack-pattern"]:
            rag_manager = rag_attck
            strict_query = query_builder.build_match_query("name", name, priority=False)

        if not rag_manager or not strict_query:
            continue

        # 1. First filter definite matches by setting a strict score threshold (Ground Truth)
        # Non-vector search scores are usually higher; 10 indicates very strong text relevance here
        strict_results, _ = rag_manager.perform_search_detailed(strict_query)
        ground_truth_name = None
        if strict_results and strict_results[0].get("_score", 0) > 5:
            ground_truth_name = strict_results[0].get("name")

        if not ground_truth_name:
            continue

        # 2. Use these successful samples for KNN matching and collect correct and incorrect _score values
        knn_query = query_builder.build_knn_query("name_vector", vector, priority=False)
        knn_results, _ = rag_manager.perform_search_detailed(knn_query)

        for res in knn_results:
            score = res.get("_score")
            # Record scores for correct matches
            if res.get("name") == ground_truth_name:
                stats["correct_scores"].append(score)
            else:
                # Record scores for all incorrect matches as background noise
                stats["incorrect_scores"].append(score)

    # Save computed vectors for later use
    attribute_dict.save_json()

    # 3. Statistics and analysis display
    c_scores = stats["correct_scores"]
    i_scores = stats["incorrect_scores"]

    print("\n" + "=" * 60)
    print("                KNN 匹配阈值分析报告                ")
    print("=" * 60)
    print(f"处理实体总数: {attribute_dict.get_len()}")
    print(f"筛选出的 Ground Truth 样本数 (Strict Match): {len(c_scores)}")

    if not c_scores:
        print("未找到满足严格匹配条件的样本。请增加数据量或适当调低严格匹配的阈值。")
        return

    print("\n[正确匹配 (Signal) KNN 分数统计]")
    print(f"  样本数: {len(c_scores)}")
    print(f"  最小值: {min(c_scores):.5f}")
    print(f"  最大值: {max(c_scores):.5f}")
    print(f"  平均值: {sum(c_scores) / len(c_scores):.5f}")

    if i_scores:
        print("\n[错误匹配 (Noise) KNN 分数统计]")
        print(f"  干扰项数: {len(i_scores)}")
        print(f"  最大干扰值: {max(i_scores):.5f}")
        print(f"  平均干扰值: {sum(i_scores) / len(i_scores):.5f}")

        max_noise = max(i_scores)
        min_signal = min(c_scores)

        print("\n[阈值建议]")
        if min_signal > max_noise:
            print(f"信号与噪声存在显著分界线 (区间: {max_noise:.5f} - {min_signal:.5f})。")
            print(f"--> 建议阈值: {(min_signal + max_noise) / 2:.5f}")
        else:
            print(f"信号与噪声存在重叠区域 (重叠区间: {min_signal:.5f} to {max_noise:.5f})。")
            # Find the zero-false-positive threshold
            zero_fp_threshold = max_noise + 0.00001
            tp_above = sum(1 for s in c_scores if s >= zero_fp_threshold)
            recall = tp_above / len(c_scores)
            print(f"--> 建议阈值 (为确保 0 误报): {zero_fp_threshold:.5f}")
            print(f"    在此阈值下，正确匹配召回率为: {recall:.1%} ({tp_above}/{len(c_scores)})")
    else:
        print("\nKNN 结果中未发现干扰项。")
        print(f"--> 建议阈值 (基于最小信号值): {min(c_scores):.5f}")
    print("=" * 60 + "\n")
