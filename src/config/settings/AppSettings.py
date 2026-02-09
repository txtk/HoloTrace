"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-08-10 09:29:25
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-08-10 09:39:10
FilePath: /task_manage/src/config/settings/AppSettings.py
Description: Application settings for the task management system.
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

import logging
import sys
from typing import Tuple

from loguru import logger

from config.settings.base import BaseSettings
from utils.logging import InterceptHandler


class AppSettings(BaseSettings):
    """
    Application settings class that extends BaseSettings.
    This class is used to manage application-specific settings.
    """

    # Default mode can be set here
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_db: str
    postgres_password: str

    redis_host: str
    redis_port: int
    redis_password: str

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_default_user: str
    rabbitmq_default_pass: str

    # es
    elastic_url: str
    elastic_api: str
    index_name: str
    easy_ea: str
    attck_index_name: str
    standard_malware_index_name: str
    target_malware_index_name: str

    neo4j_user: str
    neo4j_password: str
    neo4j_uri: str
    neo4j_sub_uri: str

    max_connection: int

    openct_url: str
    opencti_token: str
    misp_url: str
    misp_token: str
    misp_verify: bool

    alienvault_apikey: list

    root_dir: str
    json_dir: str
    csv_dir: str
    prompt_dir: str
    dataset_dir: str
    poml_log_dir: str
    result_log_dir: str
    fig_dir: str
    txt_dir: str
    temp_dir: str
    model_dir: str

    # llm api
    base_url_em: str
    base_url_chat: str
    api_key: str
    api_key_chat: str
    qwen_qa: str
    embedding: str
    embedding_dimension_rag: int
    embedding_dimension_att: int
    max_tokens: int
    temperature: float
    zhipu_api_key: str
    zhipu_model_name: str
    zhipu_url: str
    xm_url: str
    xm_api_key: str
    xm_model_name: str
    ds_url: str
    ds_api_key: str
    ds_model_name: str
    sc_url: str
    sc_api_key: list
    sc_model_name: str
    llm_platform: str

    test_mode_vector_match: str

    # 外部资源
    malpedia_url: str

    loggers: Tuple[str, str] = ["uvicorn.asgi", "uvicorn.access"]
    log_level: str

    def configure_logging(self):
        logging.getLogger().handlers = [InterceptHandler]
        for logger_name in self.loggers:
            logging.getLogger(logger_name).handlers = [InterceptHandler]
            logging.getLogger(logger_name).setLevel(self.log_level)
        logger.configure(handlers=[{"sink": sys.stderr, "level": self.log_level}])

    class Config:
        env_file = ".envs/base.env"
        env_file_encoding = "utf-8"
