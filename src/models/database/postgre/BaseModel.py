import re

from peewee_async import AioModel

from config import db


def make_table_name(model_class):
    model_name = model_class.__name__

    # Handle empty strings
    if not model_name:
        raise ValueError("类名不能为空")

    # Convert CamelCase to snake_case
    # Insert underscores before uppercase letters, then lowercase the result
    snake_case = re.sub("([A-Z])", r"_\1", model_name).lower()

    # Remove special characters and keep only letters, digits, and underscores
    snake_case = re.sub(r"[^a-z0-9_]", "_", snake_case)
    # Handle consecutive underscores
    snake_case = re.sub(r"_+", "_", snake_case)
    # Remove leading and trailing underscores
    snake_case = snake_case.strip("_")

    # Step 7: ensure the table name is not empty
    if not snake_case:
        raise ValueError("无法生成有效的表名")

    return snake_case


class BaseModel(AioModel):
    class Meta:
        database = db
        table_function = make_table_name
