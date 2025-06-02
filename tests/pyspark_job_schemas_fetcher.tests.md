The schemas in this case are not defined inline, instead they are stored in a JSON file.

# Table: my_db.table1

Schema: [my_db.table1](schemas/my_db/table1.json)

| id      | name   | creation   |
| ------- | ------ | ---------- |
| 1       | Joe    | 2024-10-01 |
| 2       | Peter  | 2024-09-01 |
| 3       | Mary   | 2024-10-12 |

# Table: my_db.table2

Schema: [my_db.table2](schemas/my_db/table2.json)

| id      | category | enabled |
| ------- | -------- | ------- |
| 1       | A        | true    |
| 2       | B        | false   |
| 4       | B        | true    |

# Table: my_db.my_table__expected

Schema: [my_db.my_table](schemas/my_db/my_table.json)

Input tables:
- my_db.table1
- my_db.table2

| id      | name   | creation   | category | enabled | today      |
| ------- | ------ | ---------- | -------- | ------- | ---------- |
| 1       | Joe    | 2024-10-01 | A        | true    | 2025-01-01 |
| 2       | Peter  | 2024-09-01 | B        | false   | 2025-01-01 |
