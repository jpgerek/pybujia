from typing import Final

from pyspark.sql import DataFrame, SparkSession
import pyspark.sql.functions as F


class UserActionsJob:
    DB_NAME: Final[str] = "my_db"

    # Used in the unit tests and here for reference
    INPUT_TABLES: Final[list[tuple]] = [
        (DB_NAME, "user_actions"),
    ]

    OUTPUT_TABLES: Final[list[tuple]] = [
        (DB_NAME, "output"),
    ]

    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def _transformation(self, user_actions_df: DataFrame) -> DataFrame:
        clean_df = (
            user_actions_df.withColumn("current_year_month", F.date_format("event_date", "yyyy-MM"))
            .withColumn(
                "previous_year_month",
                F.date_format(F.add_months(user_actions_df.event_date, -1), "yyyy-MM"),
            )
            .select("user_id", "current_year_month", "previous_year_month")
        )

        return (
            clean_df.alias("current")
            .join(
                clean_df.alias("previous"),
                (F.col("current.user_id") == F.col("previous.user_id"))
                & (F.col("current.previous_year_month") == F.col("previous.current_year_month")),
            )
            .groupBy(F.month(F.col("current.current_year_month")).alias("month"))
            .agg(F.count(F.lit(1)).alias("monthly_active_users"))
        )

    def _transformation_with_sql(self, user_actions_df: DataFrame) -> DataFrame:
        user_actions_df.createOrReplaceTempView("user_actions")

        return self._spark.sql(
            """
            WITH clean AS (
                SELECT
                    user_id,
                    DATE_FORMAT(event_date, 'yyyy-MM') current_year_month,
                    DATE_FORMAT(ADD_MONTHS(event_date, -1), 'yyyy-MM') previous_year_month
                FROM user_actions
                WHERE
                    event_type IN ('sign-in', 'like', 'comment')
            )
            SELECT
                MONTH(current_month.current_year_month) AS month,
                COUNT(1) AS monthly_active_users
            FROM clean AS current_month
            INNER JOIN clean AS previous_month ON
                current_month.user_id = previous_month.user_id
                AND current_month.previous_year_month = previous_month.current_year_month
            GROUP BY month
        """
        )

    def run(self) -> None:
        user_actions_df = self._spark.table(f"{self.DB_NAME}.user_actions")
        result_df = self._transformation(user_actions_df)

        result_df.write.mode("overwrite").saveAsTable(f"{self.DB_NAME}.output")
