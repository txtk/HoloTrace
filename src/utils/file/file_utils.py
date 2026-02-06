import json
import pickle
import shutil
from pathlib import Path
from typing import List, Union

import pandas as pd
import yaml


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def ensure_dir(directory: Union[str, Path]) -> None:
        """
        确保目录存在，如果不存在则创建

        Args:
            directory: 目录路径
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save_file(data: Union[dict, list, pd.DataFrame, str], file_path: Union[str, Path], file_type: str = None) -> None:
        """
        保存文件到指定路径

        Args:
            data: 要保存的数据
            file_path: 文件保存路径
            file_type: 文件类型（如果不指定则从文件路径推断）
        """
        file_path = Path(file_path)
        FileUtils.ensure_dir(file_path.parent)

        if file_type is None:
            file_type = file_path.suffix.lower()

        if file_type == ".json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        elif file_type == ".yaml" or file_type == ".yml":
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        elif file_type == ".csv":
            if isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False, encoding="utf-8")
            else:
                pd.DataFrame(data).to_csv(file_path, index=False, encoding="utf-8")

        elif file_type == ".txt":
            with open(file_path, "w", encoding="utf-8") as f:
                if isinstance(data, (list, tuple)):
                    f.write("\n".join(map(str, data)))
                else:
                    f.write(str(data))

        elif file_type == ".pkl":
            with open(file_path, "wb") as f:
                pickle.dump(data, f)

        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
    @staticmethod
    def read_file(file_path: Union[str, Path], file_type: str = ".txt", encoding: str = "utf-8", list_mode: bool = False) -> Union[dict, list, pd.DataFrame, str]:
        """
        读取文件并返回内容。根据文件类型返回不同对象：
          - .json/.yaml/.yml 返回 dict 或 list
          - .csv 返回 pandas.DataFrame
          - .txt 返回 str

        Args:
            file_path: 文件路径
            file_type: 可选的文件类型（例如 ".json"），不指定则从路径后缀推断
            encoding: 文本文件编码，默认 "utf-8"

        Returns:
            读取后的内容，类型依文件而定

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件类型
            Exception: 读取过程中其他错误会向上抛出
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if file_type is None:
            file_type = file_path.suffix.lower()

        if file_type == ".json":
            with open(file_path, "r", encoding=encoding) as f:
                return json.load(f)

        elif file_type in (".yaml", ".yml"):
            with open(file_path, "r", encoding=encoding) as f:
                return yaml.safe_load(f)

        elif file_type == ".csv":
            return pd.read_csv(file_path, encoding=encoding)

        elif file_type == ".pkl":
            with open(file_path, "rb") as f:
                return pickle.load(f)

        elif file_type == ".txt":
            with open(file_path, "r", encoding=encoding) as f:
                if list_mode:
                    return [line.strip() for line in f.readlines()]
                else:
                    return "".join(f.readlines())

        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功删除
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

    @staticmethod
    def delete_directory(directory: Union[str, Path]) -> bool:
        """
        删除目录及其所有内容

        Args:
            directory: 目录路径

        Returns:
            bool: 是否成功删除
        """
        try:
            directory = Path(directory)
            if directory.exists():
                shutil.rmtree(directory)
            return True
        except Exception as e:
            print(f"删除目录失败: {e}")
            return False

    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索子目录

        Returns:
            List[Path]: 文件路径列表
        """
        directory = Path(directory)
        if recursive:
            return list(directory.rglob(pattern))
        return list(directory.glob(pattern))
    
    @staticmethod
    def list_dir(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        列出目录中的子目录

        Args:
            directory: 目录路径
            pattern: 子目录匹配模式
            recursive: 是否递归搜索子目录

        Returns:
            List[Path]: 子目录路径列表
        """
        directory = Path(directory)
        if recursive:
            return [d for d in directory.rglob(pattern) if d.is_dir()]
        return [d for d in directory.glob(pattern) if d.is_dir()]

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        获取文件大小（字节）

        Args:
            file_path: 文件路径

        Returns:
            int: 文件大小（字节）
        """
        return Path(file_path).stat().st_size

    @staticmethod
    def get_file_extension(file_path: Union[str, Path]) -> str:
        """
        获取文件扩展名

        Args:
            file_path: 文件路径

        Returns:
            str: 文件扩展名（包含点号）
        """
        return Path(file_path).suffix.lower()

    @staticmethod
    def exist_file(file_path: Union[str, Path]) -> bool:
        """
        判断文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件是否存在
        """
        return Path(file_path).exists()
