# Advertiser status

From [https://datalemur.com/questions/updated-status](https://datalemur.com/questions/updated-status)

# Table: my_db.advertiser

| user_id | status   |
| ------- | -------- |
|`string` |`string`  |
| bing    | NEW      |
| yahoo   | NEW      |
| alibaba | EXISTING |

# Table: my_db.daily_pay

| user_id | paid           |
| ------- | -------------- |
|`string` |`decimal(38, 2)`|
| yahoo   | 45.00          |
| alibaba | 100.00         |
| target  | 13.00          |

# Table: my_db.output__expected

| user_id | new_status |
| ------- | ---------- |
|`string` |`string`    |
| bing    | CHURN      |
| yahoo   | EXISTING   |
| alibaba | EXISTING   |
