from peewee import CharField

from models.database.postgre.BaseModel import BaseModel


class ReportModel(BaseModel):
    report_id = CharField(max_length=100, null=False)
    report_name = CharField(max_length=255, null=False)
    file_path = CharField(max_length=255, null=False)
