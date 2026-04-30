import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

import aiofiles

from utils.file.file_utils import FileUtils


class JsonUtils(FileUtils):
    """JSON dataset operation class that inherits from FileUtils"""

    def __init__(self, json_path: Union[str, Path] = None, load=True):
        """
        Initialize JsonDataset

        Args:
            json_path: JSON file path, optional
        """
        super().__init__()
        self.json_path = json_path
        self.data = None
        if json_path and load:
            self.data = self.load_json(json_path)

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get the value of the specified key from JSON data

        Args:
            key: key name
            default: default value returned if the key does not exist

        Returns:
            Any: value for the key, or default if the key does not exist
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        return self.data.get(key, default)

    def set_value(self, key: str, value: Any):
        """
        Set the value of the specified key in JSON data

        Args:
            key: key name
            default: default value returned if the key does not exist

        Returns:
            Any: value for the key, or default if the key does not exist
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        self.data[key] = value

    def update(self, key: str, value: dict):
        """
        Update the value of the specified key in JSON data

        Args:
            key: key name
            value: dictionary to update

        Raises:
            ValueError: if the key does not exist or its value is not a dictionary
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if key not in self.data or not isinstance(self.data[key], dict):
            raise ValueError(f"键 '{key}' 不存在或对应的值不是字典类型")

        self.data[key].update(value)

    def load_json(self, file_path: Union[str, Path]) -> Union[Dict, List]:
        """
        Load a JSON file

        Args:
            file_path: JSON file path

        Returns:
            Union[Dict, List]: loaded JSON data

        Raises:
            FileNotFoundError: file does not exist
            json.JSONDecodeError: invalid JSON format
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
        Save a JSON file

        Args:
            data: data to save; uses self.data if None
            file_path: save path; uses self.json_path if None
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

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=file_path.parent, delete=False, suffix=".tmp"
            ) as tmp:
                temp_path = Path(tmp.name)

            async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))

            os.replace(temp_path, file_path)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def split_json(self, ratio: float, output_path: Union[str, Path] = None) -> Union[Dict, List]:
        """
            Split a JSON file and save the specified ratio of data to a new file.
            
            Args:
                ratio: Split ratio; for example, 0.1 means the first 10% of data.
                output_path: Output file path; if None, append the _split suffix to the original file name.
            
            Returns:
                Union[Dict, List]: Split data.
            
            Raises:
                ValueError: Ratio is outside 0-1 or data is empty.
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not 0 < ratio <= 1:
            raise ValueError("切分比例必须在0-1之间")

        if isinstance(self.data, list):
            # If it is a list, split by index
            split_size = int(len(self.data) * ratio)
            split_data = self.data[:split_size]
        elif isinstance(self.data, dict):
            # If it is a dictionary, split by number of key-value pairs
            items = list(self.data.items())
            split_size = int(len(items) * ratio)
            split_data = dict(items[:split_size])
        else:
            raise ValueError("不支持的数据类型，只支持list和dict")

        # Determine the output path
        if output_path is None:
            if self.json_path:
                json_path = Path(self.json_path)
                output_path = json_path.parent / f"{json_path.stem}_split{json_path.suffix}"
            else:
                raise ValueError("没有指定输出路径且没有原始文件路径")

        # Save the split data
        self.save_file(split_data, output_path, ".json")

        return split_data

    def apply_to_items(self, func: Callable, *args, **kwargs) -> Union[Dict, List]:
        """
        Apply the specified function to each item in JSON data

        Args:
            func: function to apply
            *args: positional arguments passed to the function
            **kwargs: keyword arguments passed to the function

        Returns:
            Union[Dict, List]: processed data

        Raises:
            ValueError: data is empty or the function is not callable
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not callable(func):
            raise ValueError("传入的参数不是可调用函数")

        if isinstance(self.data, list):
            # Apply the function to each element in the list
            processed_data = [func(item, *args, **kwargs) for item in self.data]
        elif isinstance(self.data, dict):
            # Apply the function to each value in the dictionary
            processed_data = {key: func(value, *args, **kwargs) for key, value in self.data.items()}
        else:
            # Apply the function to a single value
            processed_data = func(self.data, *args, **kwargs)

        return processed_data

    def apply_to_keys(self, func: Callable, *args, **kwargs) -> Dict:
        """
            Apply the specified function to each key in JSON dictionary data.
            
            Args:
                func: Function to apply.
                *args: Positional arguments passed to the function.
                **kwargs: Keyword arguments passed to the function.
            
            Returns:
                Dict: Processed dictionary data.
            
            Raises:
                ValueError: Data is empty, not a dictionary, or the function is not callable.
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not isinstance(self.data, dict):
            raise ValueError("此方法仅适用于字典类型的JSON数据")

        if not callable(func):
            raise ValueError("传入的参数不是可调用函数")

        # Apply the function to each key in the dictionary while keeping values unchanged
        processed_data = {func(key, *args, **kwargs): value for key, value in self.data.items()}
        self.data = processed_data
        return processed_data

    def get_data_info(self) -> Dict[str, Any]:
        """
        Get basic information about the JSON data

        Returns:
            Dict[str, Any]: dictionary containing data type, size, and related information
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
        Filter JSON data by condition

        Args:
            condition: filter condition function that returns a boolean

        Returns:
            Union[Dict, List]: filtered data

        Raises:
            ValueError: data is empty or the condition is not callable
        """
        if self.data is None:
            raise ValueError("没有加载数据，请先调用load_json方法")

        if not callable(condition):
            raise ValueError("过滤条件必须是可调用函数")

        if isinstance(self.data, list):
            # Filter list elements that satisfy the condition
            filtered_data = [item for item in self.data if condition(item)]
        elif isinstance(self.data, dict):
            # Filter dictionary key-value pairs that satisfy the condition
            filtered_data = {key: value for key, value in self.data.items() if condition(value)}
        else:
            # Evaluate the condition on a single value
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
