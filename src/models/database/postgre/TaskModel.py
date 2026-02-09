import datetime

from peewee import CharField, DateTimeField, IntegerField, UUIDField
from playhouse.postgres_ext import JSONField

from models.database.postgre.BaseModel import BaseModel


class TaskModel(BaseModel):
    id = UUIDField(primary_key=True, null=False)
    worker = CharField(max_length=50)
    args = JSONField(null=True)
    task_id = CharField(max_length=100, null=True)
    status = IntegerField(default=0)
    retry_times = IntegerField(default=0)
    result = JSONField(null=True)
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now)
    finish_time = DateTimeField(default=datetime.datetime.now)
