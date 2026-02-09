from peewee import CharField
from playhouse.postgres_ext import BinaryJSONField 

from models.database.postgre.BaseModel import BaseModel


class Neo4jRelationModel(BaseModel):
    id = CharField(primary_key=True)
    relation_type = CharField(max_length=255, null=False)
    start_id = CharField(max_length=255, null=False)
    properties = BinaryJSONField()
    end_id = CharField(max_length=255, null=False)
    neo4j_type = CharField(max_length=255, null=False)
