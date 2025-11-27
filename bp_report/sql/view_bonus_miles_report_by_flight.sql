-- 2) Бонусные мили по рейсам (report_miles_by_flight)
SELECT
  flight_number        AS "Номер рейса",
  departure_date       AS "Дата вылета",
  tickets_cnt          AS "Кол-во билетов",
  total_miles          AS "Начислено миль"
FROM report_miles_by_flight
WHERE report_month = (%s) AND report_year = (%s)
ORDER BY departure_date, flight_number;
