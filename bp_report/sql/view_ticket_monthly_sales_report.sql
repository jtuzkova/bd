-- 1) Продажи билетов (report_ticket_sales)
SELECT
  departure_airport    AS "Аэропорт вылета",
  class                AS "Класс",
  tickets_sold         AS "Продано билетов",
  total_revenue        AS "Общая выручка"
FROM report_ticket_sales
WHERE month = (%s) AND year = (%s)
ORDER BY total_revenue DESC, departure_airport, class;
