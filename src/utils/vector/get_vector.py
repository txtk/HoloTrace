from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from utils.file.file_utils import FileUtils


def load_vector_pkl(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    接收 pkl 文件位置，返回加载后的 pkl 文件对象（通常为字典）

    Args:
        file_path: pkl 文件的路径

    Returns:
        Dict: 存储向量的字典对象
    """
    return FileUtils.read_file(file_path, file_type=".pkl")


def get_vector_by_id(vector_dict: Dict[str, Any], entity_id: Union[str, int]) -> Optional[List[float]]:
    """
    接收 pkl 文件对象和查询 id，返回对应的向量

    Args:
        vector_dict: 由 load_vector_pkl 加载的字典对象
        entity_id: 实体 ID

    Returns:
        Optional[List[float]]: 对应的向量，如果不存在则返回 None
    """
    return vector_dict.get(str(entity_id))
