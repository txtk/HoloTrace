from peewee_async import PooledPostgresqlDatabase
from playhouse.shortcuts import ReconnectMixin


class RetryPostgresqlDatabase(ReconnectMixin, PooledPostgresqlDatabase):
    _instance = None

    @staticmethod
    def get_db_instance(db_config):
        if not RetryPostgresqlDatabase._instance:
            RetryPostgresqlDatabase._instance = RetryPostgresqlDatabase(
                db_config.get("database"),
                host=db_config.get("host"),
                user=db_config.get("user"),
                password=db_config.get("password"),
                port=db_config.get("port"),
                max_connections=3,
                autoconnect=True,
            )
        elif RetryPostgresqlDatabase._instance.database != db_config.get("database"):
            RetryPostgresqlDatabase._instance = RetryPostgresqlDatabase(
                db_config.get("database"),
                host=db_config.get("host"),
                user=db_config.get("user"),
                password=db_config.get("password"),
                port=db_config.get("port"),
            )

        return RetryPostgresqlDatabase._instance


def get_db_instance(db_config):
    db_config.update({"autorollback": True, "sql_mode": "NO_AUTO_CREATE_USER"})
    new_db = RetryPostgresqlDatabase(**db_config).get_db_instance(db_config)
    return new_db


