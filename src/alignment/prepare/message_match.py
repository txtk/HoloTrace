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
            # 搜索并返回第一个超过阈值的结果
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

    # 1. 收集所有需要 embedding 的名称
    names_to_embed = []
    items_to_process = []
    for _, value in attribute_dict.get_items():
        if value.get("processed") and not force:
            continue
        items_to_process.append(value)
        name = value.get("name", "").lower()
        if name and value.get("vector") is None:
            names_to_embed.append(name)

    # 2. 批量获取 embedding
    if names_to_embed:
        unique_names = list(set(names_to_embed))
        embeddings = get_embedding_celery(unique_names)
        name_to_vector = dict(zip(unique_names, embeddings))

        for value in items_to_process:
            name = value.get("name", "").lower()
            if value.get("vector") is None and name in name_to_vector:
                value["vector"] = name_to_vector[name]

    # 3. 执行匹配逻辑
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
    通过分析数据寻找 KNN 匹配的最佳阈值。
    1. 使用严格的文本匹配 (Score > 10) 确定 Ground Truth。
    2. 对这些样本执行 KNN 查询并记录正确结果与干扰结果的分数。
    3. 输出统计学建议，寻找 0 误报的阈值。
    """

    query_builder = QueryBuilder()

    stats = {"correct_scores": [], "incorrect_scores": []}

    # 遍历所有待匹配属性
    items = list(attribute_dict.get_items())

    # 1. 批量获取所有需要 embedding 的向量
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

        # 获取向量
        vector = value.get("vector")
        if vector is None:
            continue

        # 选择对应的 RAG 管理器和严格匹配方案
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

        # 1. 首先通过设定严格的 score 判定，筛选出一定匹配成功了的数据 (Ground Truth)
        # 非向量搜索的分数通常较高，这里设为 10 代表极大的文本相关性
        strict_results, _ = rag_manager.perform_search_detailed(strict_query)
        ground_truth_name = None
        if strict_results and strict_results[0].get("_score", 0) > 5:
            ground_truth_name = strict_results[0].get("name")

        if not ground_truth_name:
            continue

        # 2. 使用这些成功了的数据进行 KNN 匹配，并统计其中正确的 _score 和 错误的 _score
        knn_query = query_builder.build_knn_query("name_vector", vector, priority=False)
        knn_results, _ = rag_manager.perform_search_detailed(knn_query)

        for res in knn_results:
            score = res.get("_score")
            # 记录正确匹配的分数
            if res.get("name") == ground_truth_name:
                stats["correct_scores"].append(score)
            else:
                # 记录所有非正确匹配的分数（作为背景噪声）
                stats["incorrect_scores"].append(score)

    # 保存计算出的向量以便后续使用
    attribute_dict.save_json()

    # 3. 统计与分析显示
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
            # 寻找 0 误报阈值
            zero_fp_threshold = max_noise + 0.00001
            tp_above = sum(1 for s in c_scores if s >= zero_fp_threshold)
            recall = tp_above / len(c_scores)
            print(f"--> 建议阈值 (为确保 0 误报): {zero_fp_threshold:.5f}")
            print(f"    在此阈值下，正确匹配召回率为: {recall:.1%} ({tp_above}/{len(c_scores)})")
    else:
        print("\nKNN 结果中未发现干扰项。")
        print(f"--> 建议阈值 (基于最小信号值): {min(c_scores):.5f}")
    print("=" * 60 + "\n")
