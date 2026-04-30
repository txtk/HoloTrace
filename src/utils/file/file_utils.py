import json
import os
import pickle
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import pandas as pd
import yaml


class FileUtils:
    """File operation utility class"""

    @staticmethod
    def ensure_dir(directory: Union[str, Path]) -> None:
        """
        Ensure the directory exists; create it if it does not

        Args:
            directory: directory path
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save_file(
        data: Union[dict, list, pd.DataFrame, str], file_path: Union[str, Path], file_type: str = None
    ) -> None:
        """
        Save a file to the specified path

        Args:
            data: data to save
            file_path: file save path
            file_type: file type, inferred from the file path if not specified
        """
        file_path = Path(file_path)
        FileUtils.ensure_dir(file_path.parent)

        if file_type is None:
            file_type = file_path.suffix.lower()

        if file_type == ".json":
            # Atomic write: write to temp file in same directory, then replace target.
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=file_path.parent, delete=False, suffix=".tmp"
                ) as tmp:
                    json.dump(data, tmp, ensure_ascii=False, indent=4)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    temp_path = Path(tmp.name)

                os.replace(temp_path, file_path)
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink(missing_ok=True)

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
    def read_file(
        file_path: Union[str, Path], file_type: str = ".txt", encoding: str = "utf-8", list_mode: bool = False
    ) -> Union[dict, list, pd.DataFrame, str]:
        """
        Read a file and return its content. Different object types are returned by file type:
          - .json/.yaml/.yml returns dict or list
          - .csv returns pandas.DataFrame
          - .txt returns str

        Args:
            file_path: file path
            file_type: optional file type, such as ".json"; inferred from the path suffix if omitted
            encoding: text file encoding, default "utf-8"

        Returns:
            content read from the file; type depends on the file

        Raises:
            FileNotFoundError: file does not exist
            ValueError: unsupported file type
            Exception: other read errors are propagated
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
        Delete a file

        Args:
            file_path: file path

        Returns:
            bool: whether deletion succeeded
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
        Delete a directory and all of its contents

        Args:
            directory: directory path

        Returns:
            bool: whether deletion succeeded
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
        List files in a directory

        Args:
            directory: directory path
            pattern: file matching pattern
            recursive: whether to search subdirectories recursively

        Returns:
            List[Path]: list of file paths
        """
        directory = Path(directory)
        if recursive:
            return list(directory.rglob(pattern))
        return list(directory.glob(pattern))

    @staticmethod
    def list_dir(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        List subdirectories in a directory

        Args:
            directory: directory path
            pattern: subdirectory matching pattern
            recursive: whether to search subdirectories recursively

        Returns:
            List[Path]: list of subdirectory paths
        """
        directory = Path(directory)
        if recursive:
            return [d for d in directory.rglob(pattern) if d.is_dir()]
        return [d for d in directory.glob(pattern) if d.is_dir()]

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        Get file size in bytes

        Args:
            file_path: file path

        Returns:
            int: file size in bytes
        """
        return Path(file_path).stat().st_size

    @staticmethod
    def get_file_extension(file_path: Union[str, Path]) -> str:
        """
        Get the file extension

        Args:
            file_path: file path

        Returns:
            str: file extension including the dot
        """
        return Path(file_path).suffix.lower()

    @staticmethod
    def exist_file(file_path: Union[str, Path]) -> bool:
        """
        Check whether a file exists

        Args:
            file_path: file path

        Returns:
            bool: whether the file exists
        """
        return Path(file_path).exists()
