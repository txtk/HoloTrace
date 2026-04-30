from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from utils.file.file_utils import FileUtils


def load_vector_pkl(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Accept a pkl file path and return the loaded pkl object, usually a dictionary

    Args:
        file_path: path to the pkl file

    Returns:
        Dict: dictionary object storing vectors
    """
    return FileUtils.read_file(file_path, file_type=".pkl")


def get_vector_by_id(vector_dict: Dict[str, Any], entity_id: Union[str, int]) -> Optional[List[float]]:
    """
    Accept a pkl object and query id, then return the corresponding vector

    Args:
        vector_dict: dictionary object loaded by load_vector_pkl
        entity_id: entity ID

    Returns:
        Optional[List[float]]: corresponding vector, or None if it does not exist
    """
    return vector_dict.get(str(entity_id))
