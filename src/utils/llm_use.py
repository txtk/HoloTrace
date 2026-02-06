"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-08-26 21:55:27
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-08-27 09:34:23
FilePath: /entity_alignment/src/utils/llm_use.py
Description: 大模型相关工具类
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

# from models.llm import qwen
import os
import random
import time
from traceback import format_exc

from loguru import logger
from openai import APIStatusError, RateLimitError

from config import settings

# from models.llm.glm_batch import ZhipuBatch
from models.llm import chat_mappinng
from models.llm.embedding import embedding
from models.llm.qwen3 import qwen

# zhipu = ZhipuBatch()


def get_prompt(task):
    dir_path = os.path.join(settings.prompt_dir, task)
    system_path = os.path.join(dir_path, "layer_system")
    user_path = os.path.join(dir_path, "layer_user")
    input_template_path = os.path.join(dir_path, "input_template")
    with open(system_path, "r", encoding="utf-8") as f:
        system_prompt = "".join(f.readlines())
    with open(user_path, "r", encoding="utf-8") as f:
        user_prompt = "".join(f.readlines())
    with open(input_template_path, "r", encoding="utf-8") as f:
        input_template = "".join(f.readlines())
    input_templates = input_template.split("&&*")
    return system_prompt, user_prompt, input_templates


def get_prompt_by_name(task, name):
    target_path = os.path.join(settings.prompt_dir, task, name)
    with open(target_path, "r", encoding="utf-8") as f:
        prompt = "".join(f.readlines())
    return prompt


def set_prompt(template, query):
    prompt = template.format(query)
    return prompt


def get_response(system_prompt, user_prompt):
    return qwen.send_request(system_prompt, user_prompt)


def get_response_poml(poml_content):
    while True:
        try:
            models = chat_mappinng.get(settings.llm_platform)
            if isinstance(models, list):
                # 随机选取一个模型使用
                model = random.choice(models)
            else:
                model = models
            return model.send_request_poml(poml_content)
        except RateLimitError:
            logger.warning("Rate limit reached (429). Sleeping for 10s before retrying...")
            time.sleep(10)
        except APIStatusError:
            logger.error(format_exc())
            return None
        except Exception:
            logger.error(format_exc())
            time.sleep(100)


def get_embedding(text, dimensions=1024):
    if isinstance(text, list):
        return embedding.embed_documents(text, dimensions)
    return embedding.embed_query(text, dimensions)


# def get_zhipu_batch_chat(contexts, prompt_path):
#     zhipu.make_batch_file(prompt_path, contexts)
#     zhipu.handle_batch()
#     if zhipu.check_batch_status():
#         results = zhipu.get_batch_result()
#         return results
#     else:
#         return []
