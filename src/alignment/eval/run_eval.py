import json
import os
from pathlib import Path
from typing import Optional, Union

from .eval_f1 import eval_f1
from .eval_hit_and_mrr import eval_hit_and_mrr


def run_evaluation(
    file_path: Optional[Union[str, Path]],
    ground_truth_rank_key: str = "ground_truth_rank_new",
    target_attr_path: Optional[Union[str, Path]] = None,
    source_attr_path: Optional[Union[str, Path]] = None,
    print_hit: bool = True,
    print_f1: bool = False,
):
    """
    Manager function to run evaluation metrics.

    Args:
        file_path: Path to the JSON log file containing prediction results.
        ground_truth_rank_key: Key in the JSON objects validation ranks (e.g. 'ground_truth_rank' or 'ground_truth_rank_new').
        target_attr_path: Path to the target attributes JSON file (required if print_f1 is True).
        print_hit: Whether to calculate and print Hit@k and MRR metrics.
        print_f1: Whether to calculate and print F1 metrics.
    """

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return {}

    print(f"Loading data from {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return {}

    res = {}
    if print_hit:
        print("\n" + "=" * 30)
        print(f"Running Hit@k and MRR Evaluation (using key: {ground_truth_rank_key})")
        print("=" * 30)
        hit_metrics = eval_hit_and_mrr(data, rank_key=ground_truth_rank_key)
        res.update(hit_metrics)

    if print_f1:
        print("\n" + "=" * 30)
        print("Running F1 Evaluation")
        print("=" * 30)
        if not target_attr_path:
            # Try to infer or warn
            print("Warning: target_attr_path is required for F1 evaluation but not provided.")
            print("         Please provide the path to target_attributes.json.")
        elif not os.path.exists(target_attr_path):
            print(f"Error: Target attributes file not found at {target_attr_path}")
        else:
            f1_metrics = eval_f1(data, target_attr_path=target_attr_path)
            if f1_metrics:
                res.update(f1_metrics)

    if print_hit and source_attr_path and os.path.exists(source_attr_path):
        print("\n" + "=" * 60)
        print(f"【按组织分类的 Hit@1 及 MRR 统计】")
        print("=" * 60)
        from config import settings
        from utils.file.path_utils import PathUtils
        
        base_path = settings.json_dir
        group_anchors_path = PathUtils.path_concat(base_path, "group_anchors.json")
        group_report_num_path = PathUtils.path_concat(base_path, "group_report_num.json")
        try:
            with open(group_anchors_path, "r", encoding="utf-8") as f:
                group_anchors = json.load(f)
            with open(group_report_num_path, "r", encoding="utf-8") as f:
                group_report_num = json.load(f)
            with open(source_attr_path, "r", encoding="utf-8") as f:
                source_attr = json.load(f)
                
            name_to_ids = {}
            for sid, info in source_attr.items():
                if info.get("entity_type") == "intrusion-set":
                    name = info.get("group_name") or info.get("name") or str(sid)
                    if name not in name_to_ids:
                        name_to_ids[name] = []
                    name_to_ids[name].append(str(sid))
                    
            def get_stats(groups_list):
                hits = 0
                total = 0
                total_mrr = 0.0

                for name in groups_list:
                    sids = name_to_ids.get(name, [])
                    for sid in sids:
                        if sid in data:
                            rank_map = data[sid].get(ground_truth_rank_key, {})
                            if rank_map:
                                total += 1
                                best_rank = min(rank_map.values())
                                if best_rank == 1:
                                    hits += 1
                                total_mrr += 1.0 / best_rank

                acc = hits / total if total > 0 else 0
                avg_mrr = total_mrr / total if total > 0 else 0
                return acc, avg_mrr, hits, total

            print("\n[锚点对齐情况分类]")
            for cat, groups in group_anchors.items():
                acc, avg_mrr, hits, total = get_stats(groups)
                print(f"{cat:20} | Hit@1: {acc:.4f} | MRR: {avg_mrr:.4f} | ({hits}/{total})")
                res[f"group_hit1_{cat}"] = acc
                res[f"group_mrr_{cat}"] = avg_mrr

            print("\n[报告数量分布分类]")
            for cat, groups in group_report_num.items():
                acc, avg_mrr, hits, total = get_stats(groups)
                print(f"{cat:20} | Hit@1: {acc:.4f} | MRR: {avg_mrr:.4f} | ({hits}/{total})")
                res[f"group_hit1_{cat}"] = acc
                res[f"group_mrr_{cat}"] = avg_mrr
            
            print("=" * 60)
        except Exception as e:
            print(f"Warning: Failed to run group distribution evaluation -> {e}")

    return res


if __name__ == "__main__":
    # Example usage
    # run_evaluation(...)
    pass
