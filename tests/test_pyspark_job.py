import os
import shutil
import uuid

from typing import Final
from datetime import datetime

from pybujia import PyBujia

from pybujia.helpers import (
    Literal,
    compare_dfs,
    get_spark_session,
    get_table_schema,
    spark_method_test,
    spark_job_test,
)

from tests.pyspark_job import MyPySparkJob

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType


class TestPysparkJob:
    CURRENT_DIR: Final[str] = os.path.dirname(os.path.abspath(__file__))
    PYSPARK_DATA_DIR: Final[str] = os.path.join(CURRENT_DIR, "pyspark-data", str(uuid.uuid4()))
    FIXTURES_FILE = os.path.join(CURRENT_DIR, "pyspark_job.tests.md")

    _spark: SparkSession
    _current_datetime: datetime

    @classmethod
    def setup_class(cls) -> None:
        cls.teardown_class()

        cls._spark = get_spark_session(cls.PYSPARK_DATA_DIR)

        all_tables = MyPySparkJob.INPUT_TABLES + MyPySparkJob.OUTPUT_TABLES
        all_dbs = {db for db, _ in all_tables}
        for db in all_dbs:
            cls._spark.sql(f"CREATE DATABASE IF NOT EXISTS {db}")

        # Freezing time so the unit tests pass every day
        cls._current_datetime = datetime(2025, 1, 1, 9, 0, 0)
        MyPySparkJob.set_current_datetime(cls._current_datetime)

    @classmethod
    def teardown_class(cls) -> None:
        shutil.rmtree(cls.PYSPARK_DATA_DIR, ignore_errors=True)

    def test__transformation(self) -> None:
        """Test only for the transformation method"""
        spark_job = MyPySparkJob(self._spark)

        fixtures = PyBujia(self.FIXTURES_FILE, self._spark)

        table1_df = fixtures.get_dataframe("my_db.table1")
        table2_df = fixtures.get_dataframe("my_db.table2")
        today = self._current_datetime.date()

        expected_df = fixtures.get_dataframe("my_db.my_table__expected")

        result_df = spark_job._transformation(table1_df, table2_df, today)

        compare_dfs(result_df, expected_df, check_nullability=False)

    def test__transformation_with_sql(self) -> None:
        """Test only for the test__transformation_with_sql method"""
        spark_job = MyPySparkJob(self._spark)

        fixtures = PyBujia(self.FIXTURES_FILE, self._spark)

        table1_df = fixtures.get_dataframe("my_db.table1")
        table2_df = fixtures.get_dataframe("my_db.table2")
        today = self._current_datetime.date()

        expected_df = fixtures.get_dataframe("my_db.my_table__expected")

        result_df = spark_job._transformation_with_sql(table1_df, table2_df, today)

        compare_dfs(result_df, expected_df)

    def test_run(self) -> None:
        """
        Testing the whole spark job populating the tables locally
        """

        spark_job = MyPySparkJob(self._spark)

        fixtures = PyBujia(self.FIXTURES_FILE, self._spark)

        table1_df = fixtures.get_dataframe("my_db.table1")
        table1_df.write.mode("overwrite").saveAsTable("my_db.table1")

        table2_df = fixtures.get_dataframe("my_db.table2")
        table2_df.write.mode("overwrite").saveAsTable("my_db.table2")

        spark_job.run()

        result_df = self._spark.table("my_db.my_table")

        expected_df = fixtures.get_dataframe("my_db.my_table__expected")

        compare_dfs(result_df, expected_df)

    def test_spark_method_transformation(self) -> None:
        fixtures = PyBujia(
            self.FIXTURES_FILE,
            self._spark,
        )
        spark_job = MyPySparkJob(self._spark)
        spark_method_test(
            spark_job._transformation,
            fixtures,
            input_kwargs={
                "table1_df": "my_db.table1",
                "table2_df": "my_db.table2",
                "today": Literal(self._current_datetime.date()),
            },
            expected_result="my_db.my_table__expected",
        )

    def test_spark_method_transformation_multi_return(self) -> None:
        fixtures = PyBujia(
            self.FIXTURES_FILE,
            self._spark,
        )
        spark_job = MyPySparkJob(self._spark)
        spark_method_test(
            spark_job._transformation_multi_return,
            fixtures,
            input_args=[
                "my_db.table1",
                "my_db.table2",
                Literal(self._current_datetime.date()),
            ],
            expected_result=["my_db.my_table__expected", Literal(10.0)],
        )

    def test_spark_job(self) -> None:
        """
        Testing the whole spark job populating the tables locally
        It's the same as test_run but using the generic test instead of
        implementing it manually
        """
        fixtures = PyBujia(
            self.FIXTURES_FILE,
            self._spark,
        )
        spark_job_test(
            self._spark,
            MyPySparkJob.INPUT_TABLES,
            MyPySparkJob.OUTPUT_TABLES,
            lambda: MyPySparkJob(self._spark).run(),
            fixtures,
        )

    @classmethod
    def schemas_fetcher(cls, table_name: str) -> StructType:
        db_name, table_name, *_ = table_name.split(".")
        base_path = os.path.join(cls.CURRENT_DIR, "schemas")
        return get_table_schema(db_name, table_name, base_path)

    def test_spark_job_with_schemas_fetcher(self) -> None:
        """
        Testing the whole spark job populating the tables locally
        """
        fixtures = PyBujia(
            os.path.join(self.CURRENT_DIR, "pyspark_job_schemas_fetcher.tests.md"),
            self._spark,
            self.schemas_fetcher,
        )
        spark_job_test(
            self._spark,
            MyPySparkJob.INPUT_TABLES,
            MyPySparkJob.OUTPUT_TABLES,
            lambda: MyPySparkJob(self._spark).run(),
            fixtures,
        )
