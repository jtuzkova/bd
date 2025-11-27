SELECT
    p.p_id,
    p.name,
    p.birthday,
    p.bonus_miles,
    p.change_date
FROM passenger p
WHERE p.bonus_miles BETWEEN %s AND %s
ORDER BY p.bonus_miles DESC;