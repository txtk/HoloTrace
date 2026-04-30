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
    Calculate the similarity of two strings after removing symbols, and check whether it exceeds the threshold.
    
    Args:
        str1 (str): first string
        str2 (str): second string
        threshold (float): decision threshold, default 0.9 (90%)
        
    Returns:
        dict: contains whether it matches (bool), similarity score (float), and cleaned strings
    """
    
    # 1. Cleaning function: remove all non-letter and non-digit characters and lowercase the result
    def clean_string(text):
        # Regex [^a-zA-Z0-9] matches all characters except letters and digits
        # Replace those characters with an empty string
        return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

    # 2. Get the cleaned strings
    s1_clean = clean_string(str1)
    s2_clean = clean_string(str2)
    
    # Edge-case handling: if the cleaned result is empty
    if not s1_clean and not s2_clean:
        return False
    if not s1_clean or not s2_clean:
        return False

    # 3. Calculate similarity
    # SequenceMatcher.ratio() returns a float in [0, 1]
    similarity = SequenceMatcher(None, s1_clean, s2_clean).ratio()
    
    # 4. Determine the result
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