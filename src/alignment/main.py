import asyncio
from os import path

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
from .prepare.prepare import pre_process
from .profile.get_profile import profile


def align(suffix, test_mode=False, recreate=False):
    mine_dir = PathUtils.path_concat(settings.dataset_dir, suffix, "traditional_save")
    source_triple_path = path.join(mine_dir, "source_tuples.txt")
    target_attribute_path = path.join(mine_dir, "target_attributes.json")
    source_attribute_path = path.join(mine_dir, "source_attributes.json")
    source_target_path = path.join(mine_dir, "target_source_labels.json")
    if test_mode:
        match_mode = match_mode_test
    elif suffix != "aadm":
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
            intrusio_set_mode=True,
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
                source_attr_path=source_attribute_path,
                print_hit=True,
                print_f1=True,
            )
            run_results[mode_key][i] = metrics

    return run_results


async def generate_profile(suffix, rag_malware, rag_attck, rag_group, recreate=False):
    mine_dir = PathUtils.path_concat(settings.dataset_dir, suffix, "traditional_save")
    target_triple_path = path.join(mine_dir, "target_tuples.txt")
    source_triple_path = path.join(mine_dir, "source_tuples.txt")
    target_attribute_path = path.join(mine_dir, "target_attributes.json")
    source_attribute_path = path.join(mine_dir, "source_attributes.json")
    target_id_dict_path = path.join(mine_dir, "target_entity_type_id.json")
    source_id_dict_path = path.join(mine_dir, "source_entity_type_id.json")
    target_vector_path = path.join(mine_dir, "target_vectors.pkl")
    source_vector_path = path.join(mine_dir, "source_vectors.pkl")
    last_items = JsonUtils(path.join(settings.json_dir, f"layer_{suffix}.json")).get_value("all")
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
    # await tokenizer(suffix, mine_dir)
    # await test(suffix, mine_dir)


async def main():
    import time

    import numpy as np

    rag_malware = ElasticsearchVectorManager(index_name="rag_malware", mappings=malware_mappings)
    rag_attck = ElasticsearchVectorManager(index_name="rag_attck", mappings=attck_mappings)
    rag_group = ElasticsearchVectorManager(index_name="rag_group", mappings=group_mappings)

    suffix = "heaa_time"
    mine_dir = PathUtils.path_concat(settings.dataset_dir, suffix, "traditional_save")

    # Run preprocessing only once to avoid repeating expensive steps across experiment runs.
    # pre_process(suffix, mine_dir, "source", rag_malware, rag_attck, rag_group, force=False)
    # pre_process(suffix, mine_dir, "target", rag_malware, rag_attck, rag_group, force=False)

    all_runs_results = []
    run_times = []
    run_tokens = []

    import utils.llm_use
    num_runs = 5
    for run_idx in range(num_runs):
        logger.info(f"======== 第 {run_idx + 1} / {num_runs} 次整体流程运行开始 ========")
        start_time = time.time()
        utils.llm_use.reset_total_tokens()
        # Force regeneration of profiles and matching results to capture LLM randomness and compute averages
        # await generate_profile(suffix, rag_malware, rag_attck, rag_group, recreate=True)
        run_res = align(suffix, test_mode=False, recreate=True)
        end_time = time.time()
        duration = end_time - start_time
        used_tokens = utils.llm_use.get_total_tokens()

        logger.info(f"本次运行耗时: {duration:.2f} 秒, API调用消耗 token 数量: {used_tokens}")
        run_times.append(duration)
        run_tokens.append(used_tokens)
        all_runs_results.append(run_res)

    # Summarize results
    if not all_runs_results:
        return

    out_text = []
    out_text.append(f"\n平均运行耗时: {np.mean(run_times):.2f} 秒")
    out_text.append(f"平均消耗 Token 数量: {np.mean(run_tokens):.2f}")

    # Structure: all_runs_results -> [run1_dict, run2_dict, ...]
    # run_dict -> { mode_key: { gt_key: { metric: val } } }

    # Get all mode and GT attribute keys
    sample_res = all_runs_results[0]
    for mode_key, gt_dict in sample_res.items():
        out_text.append("\n==================================================")
        out_text.append(f"模式平均性能 (ioc={mode_key[0]}, hybrid={mode_key[1]}, profile={mode_key[2]}, top_k={mode_key[3]})")
        out_text.append("==================================================")
        for gt_key in gt_dict.keys():
            out_text.append(f"Ground Truth Key: {gt_key}")
            # Collect all metrics for this mode and GT key across 5 runs
            aggregated_metrics = {}
            for run_res in all_runs_results:
                metrics = run_res.get(mode_key, {}).get(gt_key, {})
                for m_name, m_val in metrics.items():
                    if m_name not in aggregated_metrics:
                        aggregated_metrics[m_name] = []
                    aggregated_metrics[m_name].append(m_val)

            # Calculate and print the averages
            for m_name, m_vals in aggregated_metrics.items():
                avg_val = np.mean(m_vals)
                out_text.append(f"  {m_name}: {avg_val:.4f}")

    final_output = "\n".join(out_text)
    print(final_output)

    output_file_path = path.join(mine_dir, "evaluate_results.txt")
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(final_output)
    logger.info(f"评估结果已保存至: {output_file_path}")
    # await generate_profile("mine")
    # check()


if __name__ == "__main__":
    asyncio.run(main())
