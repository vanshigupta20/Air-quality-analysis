-- =====================================================================
-- 02_queries.sql : analysis queries (SELECT, JOIN, GROUP BY, subqueries,
-- window functions, set operators). The Streamlit "SQL Explorer" tab
-- reads this file, so keep the "-- name:" / "-- title:" / "-- concept:"
-- header lines above every query.
-- =====================================================================

-- name: top_polluted_cities
-- title: Top 10 most polluted cities (average AQI)
-- concept: JOIN, GROUP BY, ORDER BY, LIMIT
SELECT c.city_name,
       ROUND(AVG(r.aqi), 1) AS avg_aqi,
       COUNT(*)             AS days_recorded
FROM air_readings r
JOIN cities c ON c.city_id = r.city_id
GROUP BY c.city_name
ORDER BY avg_aqi DESC
LIMIT 10;

-- name: seasonal_pm25
-- title: Average PM2.5 per city per season
-- concept: CASE expression via view, GROUP BY on two columns
SELECT city_name,
       season,
       ROUND(AVG(pm25), 2) AS avg_pm25
FROM v_readings
GROUP BY city_name, season
ORDER BY city_name, FIELD(season, 'Winter', 'Summer', 'Monsoon', 'Post-monsoon');

-- name: yearly_trend
-- title: Year-wise average AQI (all cities)
-- concept: Aggregate functions, GROUP BY year
SELECT yr AS year,
       ROUND(AVG(aqi), 1) AS avg_aqi,
       ROUND(MAX(aqi), 0) AS max_aqi,
       COUNT(*)           AS readings
FROM v_readings
GROUP BY yr
ORDER BY yr;

-- name: poor_days
-- title: Share of Poor, Very Poor or Severe days per city
-- concept: Conditional aggregation, IN, calculated column
SELECT city_name,
       COUNT(*) AS total_days,
       SUM(CASE WHEN aqi_bucket IN ('Poor', 'Very Poor', 'Severe') THEN 1 ELSE 0 END) AS bad_days,
       ROUND(100 * SUM(CASE WHEN aqi_bucket IN ('Poor', 'Very Poor', 'Severe') THEN 1 ELSE 0 END) / COUNT(*), 1) AS bad_days_pct
FROM v_readings
GROUP BY city_name
ORDER BY bad_days_pct DESC;

-- name: above_average_cities
-- title: Cities whose average AQI is above the overall average
-- concept: Sub-query in HAVING
SELECT c.city_name,
       ROUND(AVG(r.aqi), 1) AS avg_aqi
FROM air_readings r
JOIN cities c ON c.city_id = r.city_id
GROUP BY c.city_name
HAVING AVG(r.aqi) > (SELECT AVG(aqi) FROM air_readings)
ORDER BY avg_aqi DESC;

-- name: all_cities_left_join
-- title: All cities with their number of readings (LEFT JOIN)
-- concept: LEFT JOIN keeps cities that have no readings
SELECT c.city_name,
       COUNT(r.reading_id) AS total_readings,
       MIN(r.reading_date) AS first_reading,
       MAX(r.reading_date) AS last_reading
FROM cities c
LEFT JOIN air_readings r ON r.city_id = c.city_id
GROUP BY c.city_name
ORDER BY total_readings DESC;

-- name: worst_day_per_city
-- title: Worst pollution day for every city
-- concept: Window function ROW_NUMBER() with PARTITION BY
SELECT city_name, reading_date, aqi, aqi_bucket
FROM (
  SELECT city_name, reading_date, aqi, aqi_bucket,
         ROW_NUMBER() OVER (PARTITION BY city_name ORDER BY aqi DESC) AS rn
  FROM v_readings
) ranked
WHERE rn = 1
ORDER BY aqi DESC;

-- name: city_rank_by_year
-- title: City ranking by average AQI for each year
-- concept: Window function RANK() OVER (PARTITION BY ...)
SELECT yr AS year,
       city_name,
       ROUND(AVG(aqi), 1) AS avg_aqi,
       RANK() OVER (PARTITION BY yr ORDER BY AVG(aqi) DESC) AS pollution_rank
FROM v_readings
GROUP BY yr, city_name
ORDER BY yr, pollution_rank;

-- name: lockdown_effect
-- title: Lockdown effect: PM2.5 from 25 Mar to 30 Apr, 2019 vs 2020
-- concept: Conditional aggregation, BETWEEN, derived column
SELECT city_name,
       ROUND(AVG(CASE WHEN yr = 2019 THEN pm25 END), 1) AS pm25_2019,
       ROUND(AVG(CASE WHEN yr = 2020 THEN pm25 END), 1) AS pm25_2020,
       ROUND(100 * (AVG(CASE WHEN yr = 2020 THEN pm25 END) - AVG(CASE WHEN yr = 2019 THEN pm25 END))
             / AVG(CASE WHEN yr = 2019 THEN pm25 END), 1) AS change_pct
FROM v_readings
WHERE (reading_date BETWEEN '2019-03-25' AND '2019-04-30')
   OR (reading_date BETWEEN '2020-03-25' AND '2020-04-30')
GROUP BY city_name
HAVING pm25_2019 IS NOT NULL AND pm25_2020 IS NOT NULL
ORDER BY change_pct;

-- name: best_and_worst_city
-- title: Most polluted and cleanest city side by side
-- concept: Set operator UNION ALL
SELECT 'Most polluted' AS label, city_name, avg_aqi
FROM (SELECT city_name, ROUND(AVG(aqi), 1) AS avg_aqi
      FROM v_readings GROUP BY city_name ORDER BY avg_aqi DESC LIMIT 1) worst
UNION ALL
SELECT 'Cleanest' AS label, city_name, avg_aqi
FROM (SELECT city_name, ROUND(AVG(aqi), 1) AS avg_aqi
      FROM v_readings GROUP BY city_name ORDER BY avg_aqi ASC LIMIT 1) best;

-- name: severe_days_cities
-- title: Cities that ever recorded a Severe day, with how many
-- concept: Sub-query with IN, GROUP BY
SELECT city_name, COUNT(*) AS severe_days
FROM v_readings
WHERE city_id IN (SELECT city_id FROM air_readings WHERE aqi_bucket = 'Severe')
  AND aqi_bucket = 'Severe'
GROUP BY city_name
ORDER BY severe_days DESC;
