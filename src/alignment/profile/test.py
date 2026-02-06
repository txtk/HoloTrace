from os import path

import poml

from CeleryManage.scheduler import celery_app
from config import settings
from config.mappings import alignment
from utils.file.json_utils import JsonUtils
from utils.llm_use import get_response_poml
from utils.vector.vector_manager import ElasticsearchVectorManager
from difflib import SequenceMatcher
import json
import re
from loguru import logger
from utils.vector.RRF import RRF_Keyword_Retriever, RRF_Semantic_Retriever, RRF_Match_Retriever
from models.database.postgre.IntrusionSets import IntrusionSets
from datetime import date

def check_string_similarity(str1, str2, threshold=0.9):
    """
    计算两个字符串的相似度（去除符号后），并判断是否超过阈值。
    
    Args:
        str1 (str): 第一个字符串
        str2 (str): 第二个字符串
        threshold (float): 判定阈值，默认为 0.9 (90%)
        
    Returns:
        dict: 包含是否匹配(bool)、相似度数值(float)和清洗后的字符串
    """
    
    # 1. 清洗数据函数：去除所有非字母和数字，并转为小写
    def clean_string(text):
        # 正则表达式：[^a-zA-Z0-9] 表示匹配除了字母和数字以外的所有字符
        # 将这些字符替换为空字符串
        return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

    # 2. 获取清洗后的字符串
    s1_clean = clean_string(str1)
    s2_clean = clean_string(str2)
    
    # 边界情况处理：如果清洗后为空
    if not s1_clean and not s2_clean:
        return False
    if not s1_clean or not s2_clean:
        return False

    # 3. 计算相似度
    # SequenceMatcher.ratio() 返回一个 [0, 1] 的浮点数
    similarity = SequenceMatcher(None, s1_clean, s2_clean).ratio()
    
    # 4. 判定结果
    is_match = similarity > threshold

    return is_match

@celery_app.task(name="task.alignment.log", ignore_result=False)
def save_error(text, result, profiles, save_path="./data/log/test/result.json"):
    log_data = JsonUtils(save_path)
    result = {
        "label_group": text["group"],
        "predicted_group": result,
        "content": text["content"],
        "profiles": profiles
    }
    log_data.set_value(str(len(log_data.data)), result)
    log_data.save_json()


@celery_app.task(name="task.alignment.match", ignore_result=False)
def match(text, profiles, prompt_path, log_path):
    group_names = [re.findall(r"'(.*?)'", i)[0] for i in profiles]
    group_names = list(set(group_names))

    if text["group"] not in group_names:
        logger.info(f"Label group '{text['group']}' not in retrieved group names.\n content: {text['content']}")
        celery_app.send_task(
            "task.alignment.log", args=[text, "无", profiles, log_path])
        return False, False
        
    top_10 = True
    context = {"target": text["content"], "profiles": profiles}
    prompt = poml.poml(prompt_path, context, format="openai_chat")
    result = get_response_poml(prompt)
    top_1 = False
    if result == text["group"]:
        top_1 = True
    else:
        is_match_result = check_string_similarity(result, text["group"])
        if is_match_result:
            top_1 = True
    if not top_1:
        logger.info(f"result: {result} \n label: {str(text['group'])}")
        celery_app.send_task(
            "task.alignment.log", args=[text, result, profiles, log_path])
    return top_1, top_10



def get_result(vector, data, keyword: bool = True, semantic: bool = True, match: bool = True):
    retrievers = []
    if keyword:
        keyword_retriver = RRF_Keyword_Retriever(keywords=data["keyword"])
        retrievers.append(keyword_retriver)
    if semantic:
        semantic_retriver = RRF_Semantic_Retriever(content=data["content"])
        retrievers.append(semantic_retriver)
    if match:
        match_retriever = RRF_Match_Retriever(content=data["content"])
        retrievers.append(match_retriever)
    
    query = vector.build_query_hybrid(retrievers)
    results = vector.perform_search(query, top_k=10)
    profiles = [str({i["_source"]["group"]: i["_source"]["content"]}) for i in results]
    return profiles



async def get_data(entity: dict, dataset_type: str):
    intrusion = await IntrusionSets.aio_get_or_none(id=entity["unique_id"])
    if intrusion is None:
        group_name = entity['name']
    else:
        group_name = intrusion.group
    message = {
        "intrusion_id": entity["unique_id"],
        "content": entity.get("profile"),
        "group": group_name,
        "keyword": entity.get("keywords"),
    }
    return message

async def prepare_data(dataset_type, root_dir):
    if dataset_type == "aadm":
        dataset_col = "aadm_target"
    else:
        dataset_col = "target"
    source_attribute_path = path.join(root_dir, "source_attributes.json")
    source_target_path = path.join(root_dir, "target_source_labels.json")
    source_attribute_dict = JsonUtils(source_attribute_path)
    source_target_dict = JsonUtils(source_target_path)
    logger.info(f"source_target_dict data length: {len(source_target_dict.data)}")
    for target_id in source_target_dict.data:
        entity = source_attribute_dict.get_value(str(target_id))
        result = await get_data(entity, dataset_col)
        yield result


async def test(dataset_type, root_dir):
    today = date.today()

    vector = ElasticsearchVectorManager(settings.index_name, alignment)
    prompt_path = path.join(settings.prompt_dir, "alignment", "direct.poml")
    task_to_run = []
    async for data in prepare_data(dataset_type, root_dir):
        profiles = get_result(vector, data, keyword=True, semantic=True, match=True)
        log_path = path.join(settings.result_log_dir, f"{dataset_type}_alignment_log_{today.strftime('%m-%d')}.json")
        task = celery_app.send_task(
            "task.alignment.match", args=[data, profiles, prompt_path, log_path])
        task_to_run.append(task)

    top_1s = []
    top_10s = []
    for task in task_to_run:
        top_1, top_10 = task.get()
        top_1s.append(top_1)
        top_10s.append(top_10)
    top_1_accuracy = sum(top_1s) / len(top_1s)
    top_10_accuracy = sum(top_10s) / len(top_10s)
    print(f"Top-1 Accuracy: {top_1_accuracy:.2%}")
    print(f"Top-10 Accuracy: {top_10_accuracy:.2%}")