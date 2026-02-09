from peewee import CharField, UUIDField

from models.database.postgre.BaseModel import BaseModel


class FilterReport(BaseModel):
    id = UUIDField(primary_key=True)
    file_path = CharField(max_length=255, null=False)
    group = CharField(max_length=255, null=False)
    mask_name = CharField(max_length=255, null=False)
