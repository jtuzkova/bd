SELECT s_id, miles
FROM scale
WHERE %s BETWEEN min_price AND max_price
LIMIT 1
