SELECT h.h_date, p.name, h.old, h.new
FROM history h
JOIN passenger p ON h.pass_id = p.p_id
WHERE p.name = %s
ORDER BY h.h_date DESC
LIMIT 20;