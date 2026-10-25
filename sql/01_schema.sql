-- =====================================================================
-- 01_schema.sql : DDL for the Air Quality project (MySQL 8)
-- Run from VS Code via "python -m src.load_to_mysql" or paste into
-- MySQL Workbench and execute (lightning bolt button).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS air_quality_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE air_quality_db;

-- Drop in dependency order so the script can be re-run safely
DROP VIEW  IF EXISTS v_readings;
DROP TABLE IF EXISTS air_readings;
DROP TABLE IF EXISTS cities;

-- ---------------------------------------------------------------------
-- Table 1: cities (one row per city)
-- ---------------------------------------------------------------------
CREATE TABLE cities (
  city_id    INT AUTO_INCREMENT PRIMARY KEY,
  city_name  VARCHAR(50) NOT NULL UNIQUE,
  latitude   DECIMAL(9,6) NULL,
  longitude  DECIMAL(9,6) NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table 2: air_readings (one row per city per day)
-- ---------------------------------------------------------------------
CREATE TABLE air_readings (
  reading_id    INT AUTO_INCREMENT PRIMARY KEY,
  city_id       INT NOT NULL,
  reading_date  DATE NOT NULL,
  pm25          DECIMAL(8,2) NULL,
  pm10          DECIMAL(8,2) NULL,
  no_gas        DECIMAL(8,2) NULL,
  no2           DECIMAL(8,2) NULL,
  nox           DECIMAL(8,2) NULL,
  nh3           DECIMAL(8,2) NULL,
  co            DECIMAL(8,2) NULL,
  so2           DECIMAL(8,2) NULL,
  o3            DECIMAL(8,2) NULL,
  benzene       DECIMAL(8,2) NULL,
  toluene       DECIMAL(8,2) NULL,
  xylene        DECIMAL(8,2) NULL,
  aqi           DECIMAL(8,2) NOT NULL,
  aqi_bucket    VARCHAR(20)  NOT NULL,
  CONSTRAINT fk_reading_city FOREIGN KEY (city_id) REFERENCES cities(city_id),
  CONSTRAINT uq_city_date UNIQUE (city_id, reading_date),
  CONSTRAINT chk_aqi CHECK (aqi >= 0),
  INDEX idx_reading_date (reading_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- View: readings joined with city name, year, month and season
-- Seasons: Winter Dec-Feb, Summer Mar-May, Monsoon Jun-Sep,
--          Post-monsoon Oct-Nov
-- ---------------------------------------------------------------------
CREATE VIEW v_readings AS
SELECT
  r.reading_id,
  c.city_id,
  c.city_name,
  c.latitude,
  c.longitude,
  r.reading_date,
  YEAR(r.reading_date)  AS yr,
  MONTH(r.reading_date) AS mth,
  CASE
    WHEN MONTH(r.reading_date) IN (12, 1, 2)    THEN 'Winter'
    WHEN MONTH(r.reading_date) IN (3, 4, 5)     THEN 'Summer'
    WHEN MONTH(r.reading_date) IN (6, 7, 8, 9)  THEN 'Monsoon'
    ELSE 'Post-monsoon'
  END AS season,
  r.pm25, r.pm10, r.no_gas, r.no2, r.nox, r.nh3,
  r.co, r.so2, r.o3, r.benzene, r.toluene, r.xylene,
  r.aqi,
  r.aqi_bucket
FROM air_readings r
JOIN cities c ON c.city_id = r.city_id;
