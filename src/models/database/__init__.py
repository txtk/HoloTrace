from config import db
from models.database.postgre.FilterReport import FilterReport
from models.database.postgre.PromptPath import PromptPath
from models.database.postgre.ReportModel import ReportModel
from models.database.postgre.TaskModel import TaskModel
from models.database.postgre.Profiles import Profiles
from models.database.postgre.ProfilesTest import ProfilesTest
from models.database.postgre.Neo4jRelationModel import Neo4jRelationModel
from models.database.postgre.Neo4jEntityModel import Neo4jEntityModel
from models.database.postgre.IntrusionSets import IntrusionSets

with db.allow_sync():
    # Create the TaskModel table if it doesn't exist
    TaskModel.create_table(fail_silently=True)
    # Create the ReportModel table if it doesn't exist
    ReportModel.create_table(fail_silently=True)
    # Create the FilterReport table if it doesn't exist
    FilterReport.create_table(fail_silently=True)
    # Create the PromptPath table if it doesn't exist
    PromptPath.create_table(fail_silently=True)
    # Create the Profiles table
    Profiles.create_table(fail_silently=True)
    # Create the ProfilesTest table
    ProfilesTest.create_table(fail_silently=True)
    # Neo4j 数据存储
    Neo4jEntityModel.create_table(fail_silently=True)
    Neo4jRelationModel.create_table(fail_silently=True)
    IntrusionSets.create_table(fail_silently=True)