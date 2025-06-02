import os
import shutil
import uuid

import pytest


from typing import Final
from decimal import Decimal
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from pybujia import PyBujia, DataParsingError
from pybujia.helpers import (
    Literal,
    _resolve_arg,
    compare_dicts,
    compare_dfs_data,
    compare_dfs_schemas,
    get_spark_session,
    get_table_schema,
)


class TestPyBujia:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE_FIXTURES_PATH = os.path.join(CURRENT_DIR, "pyspark_job.tests.md")
    PYSPARK_DATA_DIR: Final[str] = os.path.join(CURRENT_DIR, "pyspark-data", str(uuid.uuid4()))

    _spark: SparkSession
    _fixtures: PyBujia

    @classmethod
    def setup_class(cls) -> None:
        cls.teardown_class()

        cls._spark = get_spark_session(cls.PYSPARK_DATA_DIR)
        cls._fixtures = PyBujia(cls.FILE_FIXTURES_PATH, cls._spark)

    @classmethod
    def teardown_class(cls) -> None:
        shutil.rmtree(cls.PYSPARK_DATA_DIR, ignore_errors=True)

    def test_compare_dicts_exact_match(self):
        result = {"a": 1, "b": "foo", "c": 3.14}
        expected = {"a": 1, "b": "foo", "c": 3.14}
        compare_dicts(result, expected)

    def test_compare_dicts_float_within_tolerance(self):
        result = {"x": 1.00001}
        expected = {"x": 1.00002}
        compare_dicts(result, expected, float_abs_tol=1e-4)

    def test_compare_dicts_float_outside_tolerance(self):
        result = {"x": 1.0}
        expected = {"x": 1.1}
        with pytest.raises(AssertionError):
            compare_dicts(result, expected, float_abs_tol=1e-3)

    def test_compare_dicts_decimal_within_tolerance(self):
        result = {"y": Decimal("2.0001")}
        expected = {"y": Decimal("2.0002")}
        compare_dicts(result, expected, float_abs_tol=1e-3)

    def test_compare_dicts_missing_key_in_expected(self):
        result = {"a": 1, "b": 2}
        expected = {"a": 1}
        with pytest.raises(ValueError):
            compare_dicts(result, expected)

    def test_compare_dicts_extra_key_in_expected(self):
        result = {"a": 1}
        expected = {"a": 1, "b": 2}
        with pytest.raises(ValueError):
            compare_dicts(result, expected)

    def test_compare_dicts_non_float_mismatch(self):
        result = {"a": 1, "b": "foo"}
        expected = {"a": 1, "b": "bar"}
        with pytest.raises(AssertionError):
            compare_dicts(result, expected)

    @classmethod
    def schemas_fetcher(cls, table_name: str) -> StructType:
        db_name, table_name, *_ = table_name.split(".")
        return get_table_schema(db_name, table_name, base_path=os.path.join(cls.CURRENT_DIR, "schemas"))

    def test_compare_dfs_schemas_matching_without_nullability(self) -> None:
        schema1 = StructType(
            [
                StructField("name", StringType(), True),
                StructField("age", IntegerType(), False),
            ]
        )
        schema2 = StructType(
            [
                StructField("name", StringType(), False),  # nullability ignored
                StructField("age", IntegerType(), True),
            ]
        )
        compare_dfs_schemas(schema1, schema2, check_nullability=False)

    def test_compare_dfs_schemas_matching_with_nullability(self) -> None:
        schema1 = StructType(
            [
                StructField("name", StringType(), True),
                StructField("age", IntegerType(), False),
            ]
        )
        schema2 = StructType(
            [
                StructField("name", StringType(), True),
                StructField("age", IntegerType(), False),
            ]
        )
        compare_dfs_schemas(schema1, schema2, check_nullability=True)

    def test_compare_dfs_schemas_mismatched_column_name(self) -> None:
        schema1 = StructType(
            [
                StructField("name", StringType(), True),
            ]
        )
        schema2 = StructType(
            [
                StructField("full_name", StringType(), True),
            ]
        )
        with pytest.raises(AssertionError, match="Schemas mismatch found"):
            compare_dfs_schemas(schema1, schema2)

    def test_compare_dfs_schemas_mismatched_data_type(self) -> None:
        schema1 = StructType(
            [
                StructField("age", IntegerType(), True),
            ]
        )
        schema2 = StructType(
            [
                StructField("age", StringType(), True),
            ]
        )
        with pytest.raises(AssertionError, match="Schemas mismatch found"):
            compare_dfs_schemas(schema1, schema2)

    def test_compare_dfs_schemas_mismatched_nullability_with_check(self) -> None:
        schema1 = StructType(
            [
                StructField("age", IntegerType(), True),
            ]
        )
        schema2 = StructType(
            [
                StructField("age", IntegerType(), False),
            ]
        )
        with pytest.raises(AssertionError, match="Schemas mismatch found"):
            compare_dfs_schemas(schema1, schema2, check_nullability=True)

    def test_compare_dfs_schemas_ignore_nullability_difference(self) -> None:
        schema1 = StructType(
            [
                StructField("age", IntegerType(), True),
            ]
        )
        schema2 = StructType(
            [
                StructField("age", IntegerType(), False),
            ]
        )
        compare_dfs_schemas(schema1, schema2, check_nullability=False)

    def test_compare_dfs_schemas_column_order_matters(self) -> None:
        schema1 = StructType(
            [
                StructField("name", StringType(), True),
                StructField("age", IntegerType(), True),
            ]
        )
        schema2 = StructType(
            [
                StructField("age", IntegerType(), True),
                StructField("name", StringType(), True),
            ]
        )
        with pytest.raises(AssertionError):
            compare_dfs_schemas(schema1, schema2)

    @pytest.mark.parametrize(
        "input_value, expected_value",
        [
            (Literal(123), 123),
            (Literal("string"), "string"),
        ],
    )
    def test__resolve_args_literals(self, input_value, expected_value) -> None:
        result = _resolve_arg(input_value, self._fixtures)
        assert result == expected_value

    def test__resolve_args_table_ids(self) -> None:
        table_id = "my_db.table1"
        expected_value = self._fixtures.get_dataframe(table_id)
        compare_dfs_data(_resolve_arg(table_id, self._fixtures), expected_value)

    @pytest.mark.parametrize(
        "input_value, expected_value",
        [
            ([["---", "---"]], True),
            ([[" :---", "---:", ":---: "]], True),
            ([["--", "---"]], False),
            ([["---", "data"]], False),
            ([["---|", "---"]], False),
            ([["---"]], True),
            ([["   ---   "]], True),
            ([["---", "---", "---"]], True),
            ([["-- ", " :-- ", ":--:"]], False),
        ],
    )
    def test_is_markdown_table(self, input_value, expected_value) -> None:
        assert PyBujia._is_markdown_table(input_value) == expected_value

    @pytest.mark.parametrize(
        "header, expected_names, expected_types",
        [
            (["id`int`", "name`string`"], ["id", "name"], ["int", "string"]),
            (["col1`int`", "col2`float`", "col3`bool`"], ["col1", "col2", "col3"], ["int", "float", "bool"]),
            (["col1", "col2"], ["col1", "col2"], []),  # No types provided, valid case
            ([" age`int` ", "  name  `string`  "], ["age", "name"], ["int", "string"]),  # Whitespace handling
        ],
    )
    def test_extract_col_names_and_types_valid(self, header, expected_names, expected_types) -> None:
        names, types_ = PyBujia._extract_col_names_and_types(header)
        assert names == expected_names
        assert types_ == expected_types

    def test_extract_col_names_and_types_mismatched(self) -> None:
        header = ["id`int`", "name"]
        with pytest.raises(DataParsingError, match="missing the data types"):
            PyBujia._extract_col_names_and_types(header)

    @pytest.mark.parametrize(
        "input_str, expected_output",
        [
            ("my_table", "my_table"),
            (" my_table ", "my_table"),
            ("[users](#users)", "users"),
            ("[ table_1 ](#link)", "table_1"),
            ("[orders](somewhere.md)", "orders"),
            ("[invalid_link]", "[invalid_link]"),
            ("[](target)", ""),
            ("[weird](link) extra", "weird"),
            ("[users](#users)[products](#products)", "users"),
        ],
    )
    def test_clean_table_schema_id(self, input_str, expected_output) -> None:
        assert PyBujia._clean_table_schema_id(input_str) == expected_output

    @pytest.mark.parametrize(
        "lines, expected",
        [
            (
                ["| id | name | age |"],
                [["id", "name", "age"]],
            ),
            (
                ["| 1 | Alice | 30 |", "| 2 | Bob | 25 |"],
                [["1", "Alice", "30"], ["2", "Bob", "25"]],
            ),
            (
                [r"| a \| b | c |"],
                [["a | b", "c"]],  # Escaped pipe becomes literal
            ),
            (
                ["| x | y |", "not a row", "| z | q |"],
                [["x", "y"], ["z", "q"]],
            ),
            (
                ["| field1 | field2 |", "| val1 | val2 | val3 |"],  # Inconsistent columns
                [["field1", "field2"], ["val1", "val2", "val3"]],
            ),
            (
                ["|  a  |  b |  c  |"],
                [["a", "b", "c"]],  # Whitespace trimmed
            ),
            (
                ["Schema: something", "random text"],  # No valid data rows
                [],
            ),
            (
                ["| escaped \\| pipe | value |"],
                [["escaped | pipe", "value"]],
            ),
        ],
    )
    def test_extract_data_lines(self, lines, expected) -> None:
        result = PyBujia._extract_data_lines(lines)
        assert result == expected

    @pytest.mark.parametrize(
        "input_schema, expected_struct",
        [
            (
                {"id": "integer", "name": "string"},
                StructType(
                    [
                        StructField("id", IntegerType(), True),
                        StructField("name", StringType(), True),
                    ]
                ),
            ),
            (
                {"active": "boolean not null", "score": "integer"},
                StructType(
                    [
                        StructField("active", BooleanType(), False),
                        StructField("score", IntegerType(), True),
                    ]
                ),
            ),
            (
                {"  username  ": "  string  not null  ", " age ": " integer "},
                StructType(
                    [
                        StructField("  username  ", StringType(), False),
                        StructField(" age ", IntegerType(), True),
                    ]
                ),
            ),
        ],
    )
    def test_convert_to_struct_type(self, input_schema, expected_struct):
        result = PyBujia._convert_to_struct_type(input_schema)
        assert result.jsonValue() == expected_struct.jsonValue()
