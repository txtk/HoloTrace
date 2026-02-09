from peewee import CharField

from models.database.postgre.BaseModel import BaseModel


class PromptPath(BaseModel):
    name = CharField(max_length=255, null=False)
    file_path = CharField(max_length=255, null=False)
    description = CharField(max_length=255, null=False)
