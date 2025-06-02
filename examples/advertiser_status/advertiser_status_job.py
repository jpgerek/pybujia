from typing import Final

from pyspark.sql import DataFrame, SparkSession
import pyspark.sql.functions as F


class AdvertiserStatusJob:
    DB_NAME: Final[str] = "my_db"

    # Used in the unit tests and here for reference
    INPUT_TABLES: Final[list[tuple]] = [
        (DB_NAME, "advertiser"),
        (DB_NAME, "daily_pay"),
    ]

    OUTPUT_TABLES: Final[list[tuple]] = [
        (DB_NAME, "output"),
    ]

    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def _transformation(self, advertiser_df: DataFrame, daily_pay_df: DataFrame) -> DataFrame:
        new_status_col = F.when(F.col("daily_pay.paid").isNull(), F.lit("CHURN")).otherwise(
            F.when(F.col("advertiser.status") == "CHURN", F.lit("RESURRECT")).otherwise(F.lit("EXISTING"))
        )
        return (
            advertiser_df.alias("advertiser")
            .join(daily_pay_df.alias("daily_pay"), "user_id", "left")
            .withColumn("new_status", new_status_col)
        ).select("user_id", "new_status")

    def _transformation_with_sql(self, advertiser_df: DataFrame, daily_pay_df: DataFrame) -> DataFrame:
        advertiser_df.createOrReplaceTempView("advertiser")
        daily_pay_df.createOrReplaceTempView("daily_pay")

        return self._spark.sql(
            """
            SELECT
                user_id,
                CASE
                    WHEN paid IS NULL THEN 'CHURN'
                    ELSE
                    CASE status
                        WHEN 'CHURN' THEN 'RESURRECT'
                        ELSE 'EXISTING'
                    END
                END AS new_status
            FROM advertiser
            LEFT JOIN daily_pay USING(user_id)
        """
        )

    def run(self) -> None:
        advertiser_df = self._spark.table(f"{self.DB_NAME}.advertiser")
        daily_pay_df = self._spark.table(f"{self.DB_NAME}.daily_pay")

        result_df = self._transformation(advertiser_df, daily_pay_df)

        result_df.write.mode("overwrite").saveAsTable(f"{self.DB_NAME}.output")
