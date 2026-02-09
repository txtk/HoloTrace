import asyncio
import time
from os import path

import numpy as np
from loguru import logger

from config import match_mode_aadm, match_mode_mine, match_mode_test, profile_mode_aadm, settings
from config import profile_mode as profile_mode_mine
from config.mappings import rag_attck as attck_mappings
from config.mappings import rag_group as group_mappings
from config.mappings import rag_malware as malware_mappings
from utils.file.json_utils import JsonUtils
from utils.file.path_utils import PathUtils
from utils.vector.vector_manager import ElasticsearchVectorManager

from .eval.run_eval import run_evaluation
from .match.match import match
from .profile.get_profile import profile
from .prepare.prepare import pre_process


def align(suffix, test_mode=False, recreate=False):
    mine_dir = PathUtils.path_concat(settings.dataset_dir, suffix)
    source_triple_path = path.join(mine_dir, "source_tuples.txt")
    target_attribute_path = path.join(mine_dir, "target_attributes.json")
    source_attribute_path = path.join(mine_dir, "source_attributes.json")
    source_target_path = path.join(mine_dir, "target_source_labels.json")
    if test_mode:
        match_mode = match_mode_test
    elif suffix == "heaa":
        match_mode = match_mode_mine
    elif suffix == "aadm":
        match_mode = match_mode_aadm
    ground_truth_name = ["ground_truth_rank_new"]

    run_results = {}

    for is_ioc, is_hybrid, profile_name, top_k in match_mode:
        results_path = match(
            suffix,
            source_target_path,
            target_attribute_path,
            source_attribute_path,
            source_triple_path,
            profile_name,
            is_ioc,
            is_hybrid,
            intrusio_set_mode=False,
            top_k=top_k,
            recreate=recreate,
        )

        mode_key = (is_ioc, is_hybrid, profile_name, top_k)
        run_results[mode_key] = {}

        for i in ground_truth_name:
            logger.info(f"开始评估结果文件: {results_path}，使用的ground_truth_rank属性为: {i}")
            metrics = run_evaluation(
                results_path,
                ground_truth_rank_key=i,
                target_attr_path=target_attribute_path,
                print_hit=True,
                print_f1=True,
            )
            run_results[mode_key][i] = metrics

    return run_results


async def generate_profile(suffix, rag_malware, rag_attck, rag_group, recreate=False):
    mine_dir = PathUtils.path_concat(settings.dataset_dir, suffix)
    target_triple_path = path.join(mine_dir, "target_tuples.txt")
    source_triple_path = path.join(mine_dir, "source_tuples.txt")
    target_attribute_path = path.join(mine_dir, "target_attributes.json")
    source_attribute_path = path.join(mine_dir, "source_attributes.json")
    target_id_dict_path = path.join(mine_dir, "target_entity_type_id.json")
    source_id_dict_path = path.join(mine_dir, "source_entity_type_id.json")
    target_vector_path = path.join(mine_dir, "target_vectors.pkl")
    source_vector_path = path.join(mine_dir, "source_vectors.pkl")
    source_target_path = path.join(mine_dir, "target_source_labels.json")
    last_items = JsonUtils(path.join(settings.json_dir, f"layer_{suffix}.json")).get_value("all")
    pre_process(suffix, mine_dir, "source", rag_malware, rag_attck, rag_group, force=False)
    pre_process(suffix, mine_dir, "target", rag_malware, rag_attck, rag_group, force=False)
    if suffix == "aadm":
        profile_mode = profile_mode_aadm
    else:
        profile_mode = profile_mode_mine
    logger.info(f"开始处理数据集: {suffix}")
    for is_profile, is_enhance, is_retriver, is_hsage, top_n, profile_name in profile_mode:
        logger.info(
            f"当前运行模式: is_profile={is_profile}, is_enhance={is_enhance}, is_retriver={is_retriver}, is_hsage={is_hsage}, profile_name={profile_name}"
        )
        profile(
            suffix,
            target_tuple_path=target_triple_path,
            source_tuple_path=source_triple_path,
            target_attribute_path=target_attribute_path,
            source_attribute_path=source_attribute_path,
            target_id_dict_path=target_id_dict_path,
            source_id_dict_path=source_id_dict_path,
            target_vector_path=target_vector_path,
            source_vector_path=source_vector_path,
            rag_malware=rag_malware,
            rag_attck=rag_attck,
            rag_group=rag_group,
            last_items=last_items,
            top_n=top_n,
            recreate=recreate,
            is_profile=is_profile,
            is_enhance_mes=is_enhance,
            is_retriver=is_retriver,
            is_hsage=is_hsage,
            profile_name=profile_name,
        )


async def main():
    rag_malware = ElasticsearchVectorManager(index_name="rag_malware", mappings=malware_mappings)
    rag_attck = ElasticsearchVectorManager(index_name="rag_attck", mappings=attck_mappings)
    rag_group = ElasticsearchVectorManager(index_name="rag_group", mappings=group_mappings)

    suffix = "heaa"
    all_runs_results = []
    run_times = []

    num_runs = 5
    for run_idx in range(num_runs):
        logger.info(f"======== 第 {run_idx + 1} / {num_runs} 次整体流程运行开始 ========")
        start_time = time.time()
        # 强制重生成画像和匹配结果，以便体现 LLM 的随机性并计算平均值
        await generate_profile(suffix, rag_malware, rag_attck, rag_group, recreate=True)
        run_res = align(suffix, test_mode=False, recreate=True)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"本次运行耗时: {duration:.2f} 秒")
        run_times.append(duration)
        all_runs_results.append(run_res)

    # 汇总结果
    if not all_runs_results:
        return

    logger.info(f"\n平均运行耗时: {np.mean(run_times):.2f} 秒")
    # 获取所有的模式和 GT 属性键
    sample_res = all_runs_results[0]
    for mode_key, gt_dict in sample_res.items():
        logger.info("\n==================================================")
        logger.info(f"模式平均性能 (ioc={mode_key[0]}, hybrid={mode_key[1]}, profile={mode_key[2]}, top_k={mode_key[3]})")
        logger.info("==================================================")
        for gt_key in gt_dict.keys():
            logger.info(f"Ground Truth Key: {gt_key}")
            # 收集 5 次运行中该模式和 GT 键下的所有指标
            aggregated_metrics = {}
            for run_res in all_runs_results:
                metrics = run_res.get(mode_key, {}).get(gt_key, {})
                for m_name, m_val in metrics.items():
                    if m_name not in aggregated_metrics:
                        aggregated_metrics[m_name] = []
                    aggregated_metrics[m_name].append(m_val)

            # 计算并打印平均值
            for m_name, m_vals in aggregated_metrics.items():
                avg_val = np.mean(m_vals)
                logger.info(f"  {m_name}: {avg_val:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
