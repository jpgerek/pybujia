# Active User Retention

From [https://datalemur.com/questions/user-retention](https://datalemur.com/questions/user-retention)

Solution tables

# Table: my_db.user_actions

| user_id | event_id | event_type | event_date          |
| ------- | -------- | ---------- | ------------------- |
|*integer*|*integer* |*string*    |*timestamp*          |
| 445     | 7765     | sign-in    | 2022-05-31 12:00:00 |
| 445     | 3634     | like       | 2022-06-05 12:00:00 |
| 648     | 3124     | like       | 2022-06-18 12:00:00 |
| 648     | 2725     | sign-in    | 2022-06-22 12:00:00 |
| 648     | 8568     | comment    | 2022-07-03 12:00:00 |
| 445     | 4363     | sign-in    | 2022-07-05 12:00:00 |
| 445     | 2425     | like       | 2022-07-06 12:00:00 |
| 445     | 2484     | like       | 2022-07-22 12:00:00 |
| 648     | 1423     | sign-in    | 2022-07-26 12:00:00 |
| 445     | 5235     | comment    | 2022-07-29 12:00:00 |
| 742     | 6458     | sign-in    | 2022-07-03 12:00:00 |
| 742     | 1374     | comment    | 2022-07-19 12:00:00 |


# Table: my_db.output__expected

| month   | monthly_active_users |
| ------- | -------------------- |
|*integer*|*long*                |
| 6       | 1                    |
| 7       | 8                    |
