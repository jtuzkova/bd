SELECT d.d_id, f.f_id, f.number, d.date, f.departure_airport, f.arrival_airport, fp.class, fp.price
FROM flight f
INNER JOIN departure d ON d.f_id = f.f_id
INNER JOIN flight_price fp ON f.f_id = fp.f_id
WHERE d.d_id = %s AND fp.class = %s
