import datetime

from pybujia.helpers import get_spark_session, compare_dfs

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    IntegerType,
    LongType,
    StructField,
    StructType,
    StringType,
    TimestampType,
)

from user_retention.user_actions_job import UserActionsJob


class TestUserActionsJob:
    _spark: SparkSession

    @classmethod
    def setup_class(cls) -> None:
        cls._spark = get_spark_session()

    def _get_user_actions_df(self) -> DataFrame:
        table_schema = StructType(
            [
                StructField("user_id", IntegerType(), True),
                StructField("event_id", IntegerType(), True),
                StructField("event_type", StringType(), True),
                StructField("event_date", TimestampType(), True),
            ]
        )

        table_data = [
            {
                "user_id": 445,
                "event_id": 7765,
                "event_type": "sign-in",
                "event_date": datetime.datetime(2022, 5, 31, 12, 0),
            },
            {
                "user_id": 445,
                "event_id": 3634,
                "event_type": "like",
                "event_date": datetime.datetime(2022, 6, 5, 12, 0),
            },
            {
                "user_id": 648,
                "event_id": 3124,
                "event_type": "like",
                "event_date": datetime.datetime(2022, 6, 18, 12, 0),
            },
            {
                "user_id": 648,
                "event_id": 2725,
                "event_type": "sign-in",
                "event_date": datetime.datetime(2022, 6, 22, 12, 0),
            },
            {
                "user_id": 648,
                "event_id": 8568,
                "event_type": "comment",
                "event_date": datetime.datetime(2022, 7, 3, 12, 0),
            },
            {
                "user_id": 445,
                "event_id": 4363,
                "event_type": "sign-in",
                "event_date": datetime.datetime(2022, 7, 5, 12, 0),
            },
            {
                "user_id": 445,
                "event_id": 2425,
                "event_type": "like",
                "event_date": datetime.datetime(2022, 7, 6, 12, 0),
            },
            {
                "user_id": 445,
                "event_id": 2484,
                "event_type": "like",
                "event_date": datetime.datetime(2022, 7, 22, 12, 0),
            },
            {
                "user_id": 648,
                "event_id": 1423,
                "event_type": "sign-in",
                "event_date": datetime.datetime(2022, 7, 26, 12, 0),
            },
            {
                "user_id": 445,
                "event_id": 5235,
                "event_type": "comment",
                "event_date": datetime.datetime(2022, 7, 29, 12, 0),
            },
            {
                "user_id": 742,
                "event_id": 6458,
                "event_type": "sign-in",
                "event_date": datetime.datetime(2022, 7, 3, 12, 0),
            },
            {
                "user_id": 742,
                "event_id": 1374,
                "event_type": "comment",
                "event_date": datetime.datetime(2022, 7, 19, 12, 0),
            },
        ]

        return self._spark.createDataFrame(table_data, table_schema)  # type: ignore

    def _get_expected_df(self) -> DataFrame:
        table_schema = StructType(
            [StructField("month", IntegerType(), True), StructField("monthly_active_users", LongType(), True)]
        )
        table_data = [{"month": 6, "monthly_active_users": 1}, {"month": 7, "monthly_active_users": 8}]
        return self._spark.createDataFrame(table_data, table_schema)  # type: ignore

    def test_old_way__transformation_with_sql(self) -> None:
        spark_job = UserActionsJob(self._spark)

        user_actions_df = self._get_user_actions_df()

        expected_df = self._get_expected_df()

        result_df = spark_job._transformation_with_sql(user_actions_df)

        compare_dfs(result_df, expected_df)

    def test_old_way__transformation(self) -> None:
        spark_job = UserActionsJob(self._spark)

        user_actions_df = self._get_user_actions_df()

        expected_df = self._get_expected_df()

        result_df = spark_job._transformation(user_actions_df)

        compare_dfs(result_df, expected_df)
