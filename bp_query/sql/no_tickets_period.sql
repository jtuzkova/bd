SELECT passenger.*
FROM passenger
LEFT JOIN (
    SELECT *
    FROM ticket
    WHERE MONTH(purchase_date) = %s
    AND YEAR(purchase_date) = %s
) tmp
USING(p_id)
WHERE t_id IS NULL;