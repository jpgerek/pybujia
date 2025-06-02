# Active User Retention

From [https://datalemur.com/questions/user-retention](https://datalemur.com/questions/user-retention)

Example tables

# Table: my_db.user_actions

| user_id | event_id | event_type | event_date          |
| ------- | -------- | ---------- | ------------------- |
|*integer*|*integer* |*string*    |*timestamp*          |
| 445     | 7765     | sign-in    | 2022-05-31 12:00:00 |
| 742     | 6458     | sign-in    | 2022-06-03 12:00:00 |
| 445     | 3634     | like       | 2022-06-05 12:00:00 |
| 742     | 1374     | comment    | 2022-06-05 12:00:00 |
| 648     | 3124     | like       | 2022-06-18 12:00:00 |


# Table: my_db.output__expected

| month   | monthly_active_users |
| ------- | -------------------- |
|*integer*|*long*                |
| 6       | 1                    |
