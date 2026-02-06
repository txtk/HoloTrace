"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-07-13
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-07-13
FilePath: /src/data_models/json_dataset.py
Description: JSON文件操作工具类，用于处理JSON文件的加载、保存、切分和数据操作

Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

import aiofiles

from utils.file.file_utils import FileUtils


class JsonUtils(FileUtils):
    """JSON数据集操作类，继承自FileUtils"""

    def __init__(self, json_path: Union[str, Path] = None, load=True):
        """
        初始化JsonDataset

        Args:
            json_path: JSON文件路径，可选参数
        """
        super().__init__()
        self.json_path = json_path
        self.data = None
        if json_path and load:
            self.data = self.load_json(json_path)

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取JSON数据中的指定键的值

        Args:
            key: 键名
            default: 如果键不存在，返回的默认值

        Returns:
            Any: 键对应的值，如果键不存在则返回default
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        return self.data.get(key, default)

    def set_value(self, key: str, value: Any):
        """
        设置JSON数据中的指定键的值

        Args:
            key: 键名
            default: 如果键不存在，返回的默认值

        Returns:
            Any: 键对应的值，如果键不存在则返回default
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        self.data[key] = value

    def update(self, key: str, value: dict):
        """
        更新JSON数据中的指定键的值

        Args:
            key: 键名
            value: 要更新的字典

        Raises:
            ValueError: 如果键不存在或对应的值不是字典类型
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if key not in self.data or not isinstance(self.data[key], dict):
            raise ValueError(f"键 '{key}' 不存在或对应的值不是字典类型")

        self.data[key].update(value)

    def load_json(self, file_path: Union[str, Path]) -> Union[Dict, List]:
        """
        加载JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            Union[Dict, List]: 加载的JSON数据

        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON格式错误
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.data = data
            self.json_path = file_path
            return data
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON文件格式错误: {e}, 文件路径{file_path}", e.doc, e.pos)

    def save_json(self, data: Union[Dict, List] = None, file_path: Union[str, Path] = None) -> None:
        """
        保存JSON文件

        Args:
            data: 要保存的数据，如果为None则使用self.data
            file_path: 保存路径，如果为None则使用self.json_path
        """
        if data is None:
            data = self.data

        if file_path is None:
            file_path = self.json_path

        if data is None:
            raise ValueError("没有数据可以保存")

        if file_path is None:
            raise ValueError("没有指定保存路径")

        self.save_file(data, file_path, ".json")

    async def save_json_async(self, data: Union[Dict, List] = None, file_path: Union[str, Path] = None) -> None:
        if data is None:
            data = self.data
        if file_path is None:
            file_path = self.json_path
        file_path = Path(file_path)
        FileUtils.ensure_dir(file_path.parent)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            # print(f"✅ 已保存到 {file_path}")

    def split_json(self, ratio: float, output_path: Union[str, Path] = None) -> Union[Dict, List]:
        """
        切分JSON文件，保存指定比例的数据到新文件

        Args:
            ratio: 切分比例，例如0.1表示前10%的数据
            output_path: 输出文件路径，如果为None则在原文件名后添加_split后缀

        Returns:
            Union[Dict, List]: 切分后的数据

        Raises:
            ValueError: 比例不在0-1范围内或数据为空
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not 0 < ratio <= 1:
            raise ValueError("切分比例必须在0-1之间")

        if isinstance(self.data, list):
            # 如果是列表，按索引切分
            split_size = int(len(self.data) * ratio)
            split_data = self.data[:split_size]
        elif isinstance(self.data, dict):
            # 如果是字典，按键值对数量切分
            items = list(self.data.items())
            split_size = int(len(items) * ratio)
            split_data = dict(items[:split_size])
        else:
            raise ValueError("不支持的数据类型，只支持list和dict")

        # 确定输出路径
        if output_path is None:
            if self.json_path:
                json_path = Path(self.json_path)
                output_path = json_path.parent / f"{json_path.stem}_split{json_path.suffix}"
            else:
                raise ValueError("没有指定输出路径且没有原始文件路径")

        # 保存切分后的数据
        self.save_file(split_data, output_path, ".json")

        return split_data

    def apply_to_items(self, func: Callable, *args, **kwargs) -> Union[Dict, List]:
        """
        对JSON数据的每个项目应用指定函数

        Args:
            func: 要应用的函数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数

        Returns:
            Union[Dict, List]: 处理后的数据

        Raises:
            ValueError: 数据为空或函数不可调用
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not callable(func):
            raise ValueError("传入的参数不是可调用函数")

        if isinstance(self.data, list):
            # 对列表中的每个元素应用函数
            processed_data = [func(item, *args, **kwargs) for item in self.data]
        elif isinstance(self.data, dict):
            # 对字典中的每个值应用函数
            processed_data = {key: func(value, *args, **kwargs) for key, value in self.data.items()}
        else:
            # 对单个值应用函数
            processed_data = func(self.data, *args, **kwargs)

        return processed_data

    def apply_to_keys(self, func: Callable, *args, **kwargs) -> Dict:
        """
        对JSON字典数据的每个键应用指定函数（仅适用于字典类型数据）

        Args:
            func: 要应用的函数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数

        Returns:
            Dict: 处理后的字典数据

        Raises:
            ValueError: 数据为空、不是字典类型或函数不可调用
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not isinstance(self.data, dict):
            raise ValueError("此方法仅适用于字典类型的JSON数据")

        if not callable(func):
            raise ValueError("传入的参数不是可调用函数")

        # 对字典中的每个键应用函数，保持值不变
        processed_data = {func(key, *args, **kwargs): value for key, value in self.data.items()}
        self.data = processed_data
        return processed_data

    def get_data_info(self) -> Dict[str, Any]:
        """
        获取JSON数据的基本信息

        Returns:
            Dict[str, Any]: 包含数据类型、大小等信息的字典
        """
        if self.data is None:
            return {"type": None, "size": 0, "empty": True}

        data_type = type(self.data).__name__

        if isinstance(self.data, (list, dict)):
            size = len(self.data)
        else:
            size = 1

        return {
            "type": data_type,
            "size": size,
            "empty": size == 0,
            "file_path": str(self.json_path) if self.json_path else None,
        }

    def filter_data(self, condition: Callable) -> Union[Dict, List]:
        """
        根据条件过滤JSON数据

        Args:
            condition: 过滤条件函数，返回布尔值

        Returns:
            Union[Dict, List]: 过滤后的数据

        Raises:
            ValueError: 数据为空或条件不可调用
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not callable(condition):
            raise ValueError("过滤条件必须是可调用函数")

        if isinstance(self.data, list):
            # 过滤列表中满足条件的元素
            filtered_data = [item for item in self.data if condition(item)]
        elif isinstance(self.data, dict):
            # 过滤字典中满足条件的键值对
            filtered_data = {key: value for key, value in self.data.items() if condition(value)}
        else:
            # 对单个值进行条件判断
            filtered_data = self.data if condition(self.data) else None

        return filtered_data

    def get_keys(self):
        return self.data.keys() if isinstance(self.data, dict) else []

    def drop_keys(self, keys: List[str]):
        if not isinstance(self.data, dict):
            raise ValueError("数据不是字典类型，无法删除键")

        for key in keys:
            self.data.pop(key, None)

    def get_items(self):
        return self.data.items() if isinstance(self.data, dict) else []
    
    def get_len(self):
        if self.data is None:
            return 0
        if isinstance(self.data, (list, dict)):
            return len(self.data)
        return 1