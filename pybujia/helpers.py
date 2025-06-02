import json
import math
import os
import inspect
from typing import Any, Callable, Optional, Union
from decimal import Decimal

from . import PyBujia

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType


DEFAULT_FLOAT_ABS_TOL: float = 1e-9


def compare_dicts(
    result_row: dict[str, Any], expected_row: dict[str, Any], float_abs_tol: float = DEFAULT_FLOAT_ABS_TOL
) -> None:
    """Compares two dictionaries field-by-field using absolute tolerance for floats.

    Args:
        result_row (dict): Actual result dictionary.
        expected_row (dict): Expected result dictionary.
        float_abs_tol (float): Absolute tolerance for float/decimal comparison.

    Raises:
        ValueError: If a key is missing in the expected row.
        AssertionError: If any value mismatches.
    """

    missing_keys = set(result_row) - set(expected_row)
    if missing_keys:
        raise ValueError(
            f"The following columns don't exist in the expected result row: {missing_keys} — {expected_row}"
        )

    extra_keys = set(expected_row) - set(result_row)
    if extra_keys:
        raise ValueError(f"The following columns are missing from the result row: {extra_keys} — {result_row}")

    for field, result_value in result_row.items():
        expected_value = expected_row[field]
        if isinstance(result_value, (float, Decimal)) and isinstance(expected_value, (float, Decimal)):
            assert math.isclose(result_value, expected_value, rel_tol=0.0, abs_tol=float_abs_tol), (
                f"Field '{field}' mismatch: {result_value} != {expected_value} "
                f"(float_abs_tol={float_abs_tol}) — Row: {result_row} vs {expected_row}"
            )
        else:
            assert result_value == expected_value, (
                f"Field '{field}' mismatch: {result_value!r} != {expected_value!r} "
                f"({type(result_value)} vs {type(expected_value)}) — Row: {result_row} vs {expected_row}"
            )


def compare_dfs_data(
    result_df: DataFrame, expected_df: DataFrame, float_abs_tol: float = DEFAULT_FLOAT_ABS_TOL
) -> None:
    """Compares two Spark DataFrames for content equality.

    Args:
        result_df (DataFrame): Actual DataFrame.
        expected_df (DataFrame): Expected DataFrame.
        float_abs_tol (float): Absolute tolerance for float/decimal comparison.

    Raises:
        AssertionError: If row counts or contents differ.
    """
    result_rows = result_df.sort(*result_df.columns).collect()
    expected_rows = expected_df.sort(*expected_df.columns).collect()

    if len(result_rows) != len(expected_rows):
        raise AssertionError(f"Row count mismatch: actual={len(result_rows)} vs expected={len(expected_rows)}")

    for row_num, (result_record, expected_record) in enumerate(zip(result_rows, expected_rows), start=1):
        try:
            compare_dicts(
                result_record.asDict(),
                expected_record.asDict(),
                float_abs_tol,
            )
        except AssertionError as ex:
            raise AssertionError(f"Mismatch in row number: {row_num}") from ex


def compare_dfs_schemas(
    result_schema: StructType,
    expected_schema: StructType,
    check_nullability: bool = False,
) -> None:
    """Compares two Spark schemas for equality.

    Args:
        result_schema (StructType): Actual schema.
        expected_schema (StructType): Expected schema.
        check_nullability (bool): Whether to include nullability in comparison.

    Raises:
        AssertionError: If schemas differ.
    """

    def schema_to_tuple_list(schema: StructType) -> list:
        return [(f.name, f.dataType.simpleString(), f.nullable if check_nullability else None) for f in schema.fields]

    result_columns = schema_to_tuple_list(result_schema)
    expected_columns = schema_to_tuple_list(expected_schema)

    assert (
        result_columns == expected_columns
    ), f"Schemas mismatch found:\nResult:   {result_schema}\nExpected: {expected_schema}"


def compare_dfs(
    result_df: DataFrame,
    expected_df: DataFrame,
    float_abs_tol: float = DEFAULT_FLOAT_ABS_TOL,
    check_nullability: bool = True,
) -> None:
    """Compares two Spark DataFrames for content and schemas equality.

    Args:
        result_df (DataFrame): Actual DataFrame.
        expected_df (DataFrame): Expected DataFrame.
        float_abs_tol (float): Absolute tolerance for float/decimal comparison.
        check_nullability (bool): Whether to include nullability in schemas comparison.

    Raises:
        AssertionError: If row counts, contents or schemas differ
    """
    compare_dfs_data(result_df, expected_df, float_abs_tol)
    compare_dfs_schemas(result_df.schema, expected_df.schema, check_nullability=check_nullability)


def get_spark_session(
    warehouse_dir: Optional[str] = None,
    extra_configs: Optional[dict[str, str]] = None,
) -> SparkSession:
    """Creates a local SparkSession configured for testing.

    Args:
        warehouse_dir (Optional[str]): Optional warehouse directory.
        extra_configs (Optional[dict[str, str]]): Additional Spark configs.

    Returns:
        SparkSession: Configured Spark session.
    """
    if warehouse_dir is None:
        caller_file = inspect.stack()[1].filename
        warehouse_dir = os.path.join(os.path.dirname(caller_file), "pyspark-data")

    configs = {
        "spark.driver.extraJavaOptions": "-Duser.timezone=GMT",
        "spark.executor.extraJavaOptions": "-Duser.timezone=GMT",
        "spark.sql.session.timeZone": "UTC",
        "spark.sql.shuffle.partitions": 1,
        "spark.sql.warehouse.dir": warehouse_dir,
    }

    if extra_configs is not None:
        configs.update(extra_configs)

    builder = SparkSession.builder.appName("unit-tests")  # type: ignore
    for key, value in configs.items():
        builder = builder.config(key, value)

    return builder.master("local[1]").getOrCreate()


def get_table_schema(db_name: str, table_name: str, base_path: str) -> StructType:
    """Loads a schema JSON file and converts it to StructType.

    Args:
        db_name (str): Database name.
        table_name (str): Table name.
        base_path (str): Root path to schemas.

    Returns:
        StructType: Parsed schema.
    """
    schema_path = os.path.join(base_path, db_name, f"{table_name}.json")
    with open(schema_path) as f:
        schema = json.load(f)

    for field in schema.get("fields", []):
        field.setdefault("metadata", {})
        field.setdefault("nullable", True)

    return StructType.fromJson(schema)


def spark_job_test(
    spark_session: SparkSession,
    input_tables: list[tuple[str, str]],
    output_tables: list[tuple[str, str]],
    run_spark_job: Callable,
    fixtures: PyBujia,
    no_assert: bool = False,
    expected_table_suffix: str = "__expected",
    float_abs_tol: float = DEFAULT_FLOAT_ABS_TOL,
    check_schemas: bool = True,
    check_schemas_nullability: bool = False,
) -> None:
    """Runs a Spark job with data populated from fixtures and validates output.

    Args:
        spark_session (SparkSession): Active Spark session.
        input_tables (list[tuple]): List of (db, table) for input.
        output_tables (list[tuple]): List of (db, table) for output.
        run_spark_job (Callable): Function that runs the Spark job.
        fixtures (PyBujia): Fixture loader instance.
        no_assert (bool): Whether to skip result assertions.
        expected_table_suffix (str): suffix for the expected tables names.
        float_abs_tol (float): Absolute tolerance for float/decimal comparison.
        check_schemas (bool): Flag to compare dataframes schemas or not.
        check_schemas_nullability (bool): Whether to check nullability in schemas comparison.

    Raises:
        AssertionError: If actual output does not match expected output.
    """

    all_required_tables = input_tables + [(db, table + expected_table_suffix) for db, table in output_tables]
    all_required_databases = {db for db, _ in all_required_tables}

    for db_name in all_required_databases:
        spark_session.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")

    for db_name, table_name in all_required_tables:
        fully_qualified_name = f"{db_name}.{table_name}"
        df = fixtures.get_dataframe(fully_qualified_name)
        df.write.mode("overwrite").saveAsTable(fully_qualified_name)

    run_spark_job()

    if no_assert:
        return

    for db_name, table_name in output_tables:
        output_table_name = f"{db_name}.{table_name}"
        expected_output_table_name = output_table_name + expected_table_suffix

        output_df = spark_session.table(output_table_name)
        expected_output_df = spark_session.table(expected_output_table_name)

        compare_dfs_data(output_df, expected_output_df, float_abs_tol)
        if check_schemas:
            compare_dfs_schemas(output_df.schema, expected_output_df.schema, check_schemas_nullability)


class Literal:
    """Wrapper for a literal value to distinguish it from fixture references.

    This is used in testing to explicitly mark input arguments or expected
    results as raw values, rather than fixture table identifiers.

    Attributes:
        _value (Any): The wrapped literal value.
    """

    def __init__(self, value: Any):
        """Initializes a Literal wrapper.

        Args:
            value (Any): The literal value to wrap.
        """
        self._value = value

    def unwrap(self) -> Any:
        """Returns the wrapped literal value.

        Returns:
            Any: The original, unwrapped value.
        """
        return self._value


def _resolve_arg(value: Union[Literal, str, Any], fixtures: PyBujia) -> Union[DataFrame, Any]:
    """Resolves an argument value, determining if it's a fixture or a literal.

    This utility function is used to normalize inputs or expected outputs
    in `spark_method_test`. It handles three cases:

    - If the value is a `Literal`, unwrap and return the contained value.
    - If the value is a string, treat it as a fixture table ID and return the corresponding DataFrame.
    - Otherwise, return the value as-is.

    Args:
        value (Union[Literal, str, Any]): The input to resolve. Can be a Literal-wrapped value,
            a fixture table name (str), or any raw value.
        fixtures (PyBujia): The fixture loader used to retrieve DataFrames for string references.

    Returns:
        Union[DataFrame, Any]: The resolved value, which may be a DataFrame or any other value.
    """
    if isinstance(value, Literal):
        return value.unwrap()
    if isinstance(value, str):
        return fixtures.get_dataframe(value)
    return value


def spark_method_test(
    method: Callable,
    fixtures: PyBujia,
    expected_result: Union[Union[str, Literal], list[Union[str, Literal]]],
    input_args: Optional[list[Union[str, Literal]]] = None,
    input_kwargs: Optional[dict[str, Union[str, Literal]]] = None,
    float_abs_tol: float = DEFAULT_FLOAT_ABS_TOL,
    check_schemas: bool = True,
    check_schemas_nullability: bool = False,
) -> None:
    """Tests any PySpark transformation method using fixture-based and literal inputs.

    Supports comparing outputs as PySpark DataFrames, numeric types with float tolerance,
    or raw values using equality.

    Args:
        method (Callable): The transformation method to test.
        fixtures (PyBujia): Fixture loader that can fetch DataFrames by table ID.
        expected_result (Union[Union[str, Literal], list[Union[str, Literal]]]): Expected output(s), either as:
            - Fixture table ID(s), or
            - Literal(...) wrapped values for direct input.
        input_args (Optional[list[Union[str, Literal]]]): List of positional arguments:
            - Fixture table IDs (str), or
            - Literal(...) wrapped values for direct input.
        input_kwargs (Optional[dict[str, Union[str, Literal]]]): List of keyword arguments:
            - Fixture table IDs (str), or
            - Literal(...) wrapped values for direct input.
        float_abs_tol (float, optional): Absolute tolerance for float/decimal comparisons.
            Defaults to DEFAULT_FLOAT_ABS_TOL.
        check_schemas (bool): Flag to compare dataframes schemas or not.
        check_schemas_nullability (bool): Whether to check nullability in schemas comparison.

    Raises:
        AssertionError: If actual and expected outputs do not match in value, structure,
            or within the specified float tolerance.
    """

    input_args = input_args or []
    input_kwargs = input_kwargs or {}

    if not isinstance(expected_result, (list, tuple)):
        expected_result = [expected_result]

    prepared_positional_args = [_resolve_arg(arg_value, fixtures) for arg_value in input_args]
    prepared_kwargs = {arg_name: _resolve_arg(arg_value, fixtures) for arg_name, arg_value in input_kwargs.items()}

    result = method(*prepared_positional_args, **prepared_kwargs)

    if not isinstance(result, (list, tuple)):
        result = [result]

    assert len(result) == len(expected_result), f"Expected {len(expected_result)} outputs, got {len(result)}"

    for res_val, res_exp_val in zip(result, expected_result):
        val = _resolve_arg(res_val, fixtures)
        val_exp = _resolve_arg(res_exp_val, fixtures)

        if isinstance(val_exp, DataFrame):
            result_df = val
            expected_df = val_exp
            compare_dfs_data(result_df, expected_df, float_abs_tol)
            if check_schemas:
                compare_dfs_schemas(result_df.schema, expected_df.schema, check_schemas_nullability)
        elif isinstance(val, (float, Decimal)) and isinstance(val_exp, (float, Decimal)):
            assert math.isclose(val, val_exp, rel_tol=0.0, abs_tol=float_abs_tol), f"mismatch: {val} != {val_exp} "
        else:
            assert val == val_exp, f"mismatch: {val} != {val_exp}"
