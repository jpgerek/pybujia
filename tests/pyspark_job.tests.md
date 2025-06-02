# Unit tests data for pyspark_job.py

# Table: my_db.table1

| id      | name   | creation   |
| ------- | ------ | ---------- |
|`integer`|`string`|`date`      |
| 1       | Joe    | 2024-10-01 |
| 2       | Peter  | 2024-09-01 |
| 3       | Mary   | 2024-10-12 |

# Table: my_db.table2

In this case the data types are defined next to the column name instead of the second row.

| id `integer`  | category `string`  | enabled `boolean`  |
| ------------- | ------------------ | ------------------ |
| 1             | A                  | true               |
| 2             | B                  | false              |
| 4             | B                  | <NULL>             |

# Table: my_db.my_table__expected

Input tables:
- my_db.table1
- my_db.table2

This table uses spark `.show()` format instead of Markdown.

```
+---------+--------+------------+----------+---------+------------+
| id      | name   | creation   | category | enabled | today      |
+---------+--------+------------+----------+---------+------------+
| integer | string | date       | string   | boolean | date       |
+---------+--------+------------+----------+---------+------------+
| 1       | Joe    | 2024-10-01 | A        | true    | 2025-01-01 |
| 2       | Peter  | 2024-09-01 | B        | false   | 2025-01-01 |
+---------+--------+------------+----------+---------+------------+
```
