from peewee import CharField

from models.database.postgre.Profiles import Profiles


class ProfilesTest(Profiles):
    group = CharField(max_length=255)
