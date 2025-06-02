from decimal import Decimal

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DecimalType,
    StringType,
    StructField,
    StructType,
)

from advertiser_status.advertiser_status_job import AdvertiserStatusJob
from pybujia.helpers import compare_dfs, get_spark_session


class TestOldWayAdvertiserJob:
    _spark: SparkSession

    @classmethod
    def setup_class(cls) -> None:
        cls._spark = get_spark_session()

    def _get_advertiser_df(self) -> DataFrame:
        table_schema = StructType(
            [StructField("user_id", StringType(), True), StructField("status", StringType(), True)]
        )
        table_data = [
            {"user_id": "bing", "status": "NEW"},
            {"user_id": "yahoo", "status": "NEW"},
            {"user_id": "alibaba", "status": "EXISTING"},
            {"user_id": "baidu", "status": "EXISTING"},
            {"user_id": "target", "status": "CHURN"},
        ]
        return self._spark.createDataFrame(table_data, table_schema)  # type: ignore

    def _get_daily_pay_df(self) -> DataFrame:
        table_schema = StructType(
            [StructField("user_id", StringType(), True), StructField("paid", DecimalType(38, 2), True)]
        )
        table_data = [
            {"user_id": "yahoo", "paid": Decimal("45.00")},
            {"user_id": "alibaba", "paid": Decimal("100.00")},
            {"user_id": "target", "paid": Decimal("13.00")},
            {"user_id": "morgan", "paid": Decimal("600.00")},
            {"user_id": "fitdata", "paid": Decimal("25.00")},
        ]
        return self._spark.createDataFrame(table_data, table_schema)  # type: ignore

    def _get_expected_df(self) -> DataFrame:
        table_schema = StructType(
            [StructField("user_id", StringType(), True), StructField("new_status", StringType(), True)]
        )
        table_data = [
            {"user_id": "bing", "new_status": "CHURN"},
            {"user_id": "yahoo", "new_status": "EXISTING"},
            {"user_id": "alibaba", "new_status": "EXISTING"},
            {"user_id": "baidu", "new_status": "CHURN"},
            {"user_id": "target", "new_status": "RESURRECT"},
        ]
        return self._spark.createDataFrame(table_data, table_schema)  # type: ignore

    def test_old_way__transformation_with_sql(self) -> None:
        spark_job = AdvertiserStatusJob(self._spark)

        advertiser_df = self._get_advertiser_df()
        daily_pay_df = self._get_daily_pay_df()

        expected_df = self._get_expected_df()

        result_df = spark_job._transformation_with_sql(advertiser_df, daily_pay_df)

        compare_dfs(result_df, expected_df)

    def test_old_way__transformation(self) -> None:
        spark_job = AdvertiserStatusJob(self._spark)

        advertiser_df = self._get_advertiser_df()
        daily_pay_df = self._get_daily_pay_df()

        expected_df = self._get_expected_df()

        result_df = spark_job._transformation_with_sql(advertiser_df, daily_pay_df)

        compare_dfs(result_df, expected_df)
