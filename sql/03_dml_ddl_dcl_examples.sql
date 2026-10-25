-- =====================================================================
-- 03_dml_ddl_dcl_examples.sql : run these by hand in MySQL Workbench
-- for the DDL / DML / DCL part of your report (take screenshots).
-- Run 01_schema.sql and load the data first.
-- =====================================================================
USE air_quality_db;

-- ---------------------------- DDL ------------------------------------
-- Add a column, then drop a helper table
ALTER TABLE cities ADD COLUMN state VARCHAR(50) NULL;

CREATE TABLE city_notes (
  note_id  INT AUTO_INCREMENT PRIMARY KEY,
  city_id  INT NOT NULL,
  note     VARCHAR(200),
  FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

-- ---------------------------- DML ------------------------------------
UPDATE cities SET state = 'Delhi'       WHERE city_name = 'Delhi';
UPDATE cities SET state = 'Maharashtra' WHERE city_name = 'Mumbai';
UPDATE cities SET state = 'Karnataka'   WHERE city_name = 'Bengaluru';
UPDATE cities SET state = 'Bihar'       WHERE city_name = 'Patna';

INSERT INTO cities (city_name, latitude, longitude, state)
VALUES ('Test City', 28.0000, 77.0000, 'Haryana');

INSERT INTO city_notes (city_id, note)
SELECT city_id, 'Added as a demo row' FROM cities WHERE city_name = 'Test City';

SELECT * FROM cities WHERE state IS NOT NULL;

-- Delete child rows first because of the foreign key
DELETE FROM city_notes WHERE city_id = (SELECT city_id FROM cities WHERE city_name = 'Test City');
DELETE FROM cities     WHERE city_name = 'Test City';

DROP TABLE city_notes;

-- ---------------------------- DCL ------------------------------------
-- Create a read-only analyst user and a data-entry user
CREATE USER IF NOT EXISTS 'aq_analyst'@'localhost' IDENTIFIED BY 'Analyst@123';
CREATE USER IF NOT EXISTS 'aq_editor'@'localhost'  IDENTIFIED BY 'Editor@123';

GRANT SELECT ON air_quality_db.*            TO 'aq_analyst'@'localhost';
GRANT SELECT, INSERT, UPDATE ON air_quality_db.air_readings TO 'aq_editor'@'localhost';
GRANT SELECT ON air_quality_db.cities       TO 'aq_editor'@'localhost';

SHOW GRANTS FOR 'aq_analyst'@'localhost';
SHOW GRANTS FOR 'aq_editor'@'localhost';

REVOKE INSERT, UPDATE ON air_quality_db.air_readings FROM 'aq_editor'@'localhost';
SHOW GRANTS FOR 'aq_editor'@'localhost';

-- Clean up
DROP USER 'aq_analyst'@'localhost';
DROP USER 'aq_editor'@'localhost';

-- ---------------------------- Data dictionary ------------------------
SELECT table_name, table_rows
FROM information_schema.tables
WHERE table_schema = 'air_quality_db';
