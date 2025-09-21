# <img src="logo-vertical.png" height="70px"/> PyBujia

![tests passing](https://github.com/jpgerek/pybujia/actions/workflows/ci.yaml/badge.svg)
![pypi version](https://img.shields.io/pypi/v/pybujia)
![python versions](https://img.shields.io/pypi/pyversions/pybujia)

Enables human-readable formats like Markdown or Spark's .show() for unit test input/expected tables - easy to document and version, making test data changes simple to track and review.
Includes helpers to make writing PySpark unit tests easier.

## Requirements

- Python >= 3.9
- PySpark >= 3.0.0
- Java JDK => 8, 11, 17 or 21
- OS Linux or macOS

## Installation

```
pip install pybujia
```

## Example

This is how readable and simple your unit tests data and documentation could look:

You can add here the requirements and details

# Table: my_db.user_actions

| user_id `integer` |  event_id `integer` |  event_type `integer` |  event_date  `timestamp`  |
| ----------------- | ------------------- | --------------------- | ------------------------- |
| 445               |  7765               |  sign-in              |  2022-05-31 12:00:00      |
| 445               |  3634               |  like                 |  2022-06-05 12:00:00      |
| 648               |  3124               |  like                 |  2022-06-18 12:00:00      |
| 648               |  2725               |  sign-in              |  2022-06-22 12:00:00      |
| 648               |  8568               |  comment              |  2022-07-03 12:00:00      |
| 445               |  4363               |  sign-in              |  2022-07-05 12:00:00      |
| 445               |  2425               |  like                 |  2022-07-06 12:00:00      |
| 445               |  2484               |  like                 |  2022-07-22 12:00:00      |
| 648               |  1423               |  sign-in              |  2022-07-26 12:00:00      |
| 445               |  5235               |  comment              |  2022-07-29 12:00:00      |
| 742               |  6458               |  sign-in              |  2022-07-03 12:00:00      |
| 742               |  1374               |  comment              |  2022-07-19 12:00:00      |

# Table: my_db.output__expected

Input table: my_db.user_actions

|  month `integer` |  monthly_active_users `long` |
| ---------------- | ---------------------------- |
|  6               |  1                           |
|  7               |  8                           |

You can add more clarifications here too.

This is how easy writing unit tests is:

```python
def test_user_actions_method_transformation(self) -> None:
    # Your Spark job
    spark_job = UserActionsJob(self._spark)

    # Getting the table fixtures defined in the file "solutions.test.md"
    fixtures = PyBujia(
        os.path.join(self.CURRENT_DIR, "solution.tests.md"),  # Fixtures file full path
        self._spark,  # Spark session
    )

    # This method is generic, it can test any transformation method
    spark_method_test(
        spark_job._transformation,  # Transformation method defined in your Spark job
        fixtures,  # Tables defined in the file "solutions.tests.md"
        input_args=["my_db.user_actions"],  # Input table name
        expected_result="my_db.output__expected",  # Output/expected table name
    )
```

If you want to test the whole job, end to end, not just a method:

```python
def test_user_actions_job_solution(self):
    # Getting the table fixtures defined in the file "solutions.test.md"
    fixtures = PyBujia(
        os.path.join(self.CURRENT_DIR, "solution.tests.md"),  # Fixtures file full path
        self._spark,  # Spark session
    )

    # This method is generic, it can test any Spark job class
    spark_job_test(
        self._spark,  # Spark session
        UserActionsJob.INPUT_TABLES,  # List of input tables
        UserActionsJob.OUTPUT_TABLES, # List of output/expected tables
        lambda: UserActionsJob(self._spark).run(),  # Callback that triggers the Spark job execution
        fixtures,  # Tables defined in the file "solutions.tests.md"
    )
```

This exact test code works for any spark job, the only difference is the input fixtures file name and Spark Job class

PySpark job implementation:

```python
from typing import Final

from pyspark.sql import DataFrame
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

    # All the transformation logic
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

    # Triggers the Spark job execution
    def run(self) -> None:
        user_actions_df = self._spark.table(f"{self.DB_NAME}.user_actions")
        result_df = self._transformation(user_actions_df)

        result_df.write.mode("overwrite").saveAsTable(f"{self.DB_NAME}.output")
```

### Running the example

- Clone PyBujia repository

```bash
git clone https://github.com/jpgerek/pybujia.git
cd pybujia
```

- Install dependencies

```bash
# Optionally you could choose a specific pyspark version
pip install pyspark==3.3.0
# Or just install the latest one
pip install pyspark

pip install ".[dev]"
```

Note: You'll need to have Java JDK >=8 installed in your OS

- Running the unit tests

```bash
PYTHONPATH=. python3 -m pytest -vvs . examples/user_retention/tests/test_user_actions.py
```

You can check the example full implementation [here](examples/user_retention/)

## Structure and Guidelines for Data Fixtures

To define a table in a data fixture, begin the line with the keyword **"Table:"** - any preceding header symbols "###" won't interfere with detection, as the parser will still interpret it correctly.

Test data rows must use the **pipe symbol (`|`)** as the leading character. This symbol also separates individual column values, operating much like a comma in a CSV file.

In cases where you need an actual pipe character as part of a column's content, escape it with a backslash: `\|`.

To denote a NULL value, write it as `<NULL>`

Markdown formatting is fully supported. You can embed links, images, or add human-friendly notes to make the fixture files easier to understand.

The inline data types must be PySpark valid.

This format plays a dual role - it doubles as test documentation and actual input for executing unit tests.

Some examples:

- [Different ways to define tables and its schemas](tests/pyspark_job.tests.md)
- [Defining the schemas externally as JSON files](tests/pyspark_job_schemas_fetcher.tests.md)
- [2 input tables and 1 output table](examples/advertiser_status/tests/solution.tests.md)
- [1 input table and 1 output table](examples/user_retention/tests/solution.tests.md)

## Notes

"Bujía" in Spanish (pronounced boo-HEE-ah) means spark plug.

This project was built independently as a flexible, general-purpose toolkit for PySpark unit testing.
