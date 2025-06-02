from typing import Final
from datetime import datetime, date

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import lit


class MyPySparkJob:
    DB_NAME: Final[str] = "my_db"

    # Used in the unit tests and here for reference
    INPUT_TABLES: Final[list[tuple[str, str]]] = [
        (DB_NAME, "table1"),
        (DB_NAME, "table2"),
    ]
    OUTPUT_TABLES: Final[list[tuple[str, str]]] = [
        (DB_NAME, "my_table"),
    ]

    _current_datetime = datetime.now()

    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def _transformation(self, table1_df: DataFrame, table2_df: DataFrame, today: date) -> DataFrame:
        return table1_df.join(table2_df, ["id"]).withColumn("today", lit(today))

    def _transformation_multi_return(
        self, table1_df: DataFrame, table2_df: DataFrame, today: date
    ) -> tuple[DataFrame, float]:
        return table1_df.join(table2_df, ["id"]).withColumn("today", lit(today)), 10.0

    def _transformation_with_sql(self, table1_df: DataFrame, table2_df: DataFrame, today: date) -> DataFrame:
        """
        Equivalent implementation of the method _transformation just
        using spark SQL api, instead
        """
        table1_df.createOrReplaceTempView("table1")
        table2_df.createOrReplaceTempView("table2")

        return self._spark.sql(
            f"""
            SELECT
                *,
                CAST('{today}' AS DATE) AS today
            FROM table1
            INNER JOIN table2 USING(id)
        """
        )

    @classmethod
    def set_current_datetime(cls, new_datetime: datetime) -> None:
        """
        Method to set a custom current datetime in the unit tests,
        so the unit tests pass every day
        """
        cls._current_datetime = new_datetime

    def run(self) -> None:
        table1_df = self._spark.table(f"{self.DB_NAME}.table1")
        table2_df = self._spark.table(f"{self.DB_NAME}.table2")
        result_df = self._transformation(table1_df, table2_df, today=self._current_datetime.date())

        result_df.write.mode("overwrite").saveAsTable(f"{self.DB_NAME}.my_table")
