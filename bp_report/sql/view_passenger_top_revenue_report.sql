-- 3) ТОП пассажиров по выручке (passenger_monthly_revenue_reports)
SELECT
  passenger_name       AS "Имя пассажира",
  tickets_cnt          AS "Кол-во билетов",
  total_revenue        AS "Общая выручка"
FROM passenger_monthly_revenue_reports
WHERE report_month = (%s) AND report_year = (%s)
ORDER BY total_revenue DESC, tickets_cnt DESC, p_id;
