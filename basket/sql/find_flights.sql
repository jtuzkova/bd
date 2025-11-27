SELECT d.d_id, f.f_id, f.number, d.date, f.departure_airport, f.arrival_airport, fp.class, fp.price
FROM flight f
INNER JOIN departure d ON f.f_id = d.f_id
INNER JOIN flight_price fp ON f.f_id = fp.f_id
WHERE f.arrival_airport = %s
  AND fp.class = %s
  AND d.date = %s
  AND f.departure_airport = %s
ORDER BY fp.price ASC