import json
from pathlib import Path
from typing import Union

from pydantic import BaseModel

from models.database.neo4j.base import NodeWithName
from models.database.neo4j.report import Report
from models.database.neo4j.tuple import Tuple
from .ioc import IoC
from utils.file.file_utils import FileUtils


class TotalReport(BaseModel):
    report: Union[Report, NodeWithName, IoC]
    related_tuples: list[Tuple] = []


    def add_related_tuple(self, start, end, relation):
        new_tuple = Tuple(start=start, end=end, relation=relation)
        self.related_tuples.append(new_tuple)

    def save_data(self, path: str):
        file_path = Path(path)
        FileUtils.ensure_dir(file_path.parent)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
