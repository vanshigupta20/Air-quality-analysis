# Air Quality Analysis of Indian Cities

Data analytics mini project: **Excel (cleaning, pivots, outliers) + MySQL (storage, SQL analysis) + Streamlit (dashboard)**.

Dataset: *Air Quality Data in India (2015 - 2020)* on Kaggle (file `city_day.csv`, 26 cities, daily readings of PM2.5, PM10, NO2, SO2, CO, O3, AQI and more).

---

## 1. Project structure

```
air_quality_project/
├── app/
│   └── dashboard.py            Streamlit dashboard (6 tabs)
├── data/
│   ├── raw/                    put the Kaggle city_day.csv here
│   ├── processed/              cleaned CSV is created here
│   └── sample/                 synthetic test data (NOT for your report)
├── sql/
│   ├── 01_schema.sql           DDL: database, 2 tables, 1 view
│   ├── 02_queries.sql          11 analysis queries (joins, subqueries, window functions)
│   └── 03_dml_ddl_dcl_examples.sql   ALTER / INSERT / UPDATE / DELETE / GRANT / REVOKE
├── src/
│   ├── config.py               paths + reads the .env file
│   ├── db.py                   MySQL connection helper
│   ├── clean_data.py           step 1: clean the raw CSV
│   ├── load_to_mysql.py        step 2: create tables and load data
│   ├── test_connection.py      checks Python can reach MySQL
│   ├── city_coords.py          latitude/longitude of the 26 cities (for the map)
│   └── make_sample_data.py     creates synthetic data for testing only
├── .env.example                copy to .env and add your MySQL password
├── requirements.txt
└── README.md
```

**How the pieces connect**

```
Kaggle CSV -> clean_data.py -> cleaned CSV -> load_to_mysql.py -> MySQL (air_quality_db)
                                                                      |
                              MySQL Workbench (run / screenshot SQL) -+- Streamlit dashboard
```

---

## 2. One-time setup in VS Code (Windows)

### 2.1 Install what you need
1. **Python 3.11 or 3.12** (3.12 is what this project was tested on; pandas 3 needs 3.11 or newer) from python.org (tick *Add Python to PATH* during install).
2. **VS Code** with the extensions **Python** and (optional) **SQLTools**.
3. **MySQL Community Server** and **MySQL Workbench** (you already have both).

### 2.2 Open the project
`File > Open Folder...` and choose the `air_quality_project` folder. Open a terminal with `` Ctrl + ` ``.

### 2.3 Create a virtual environment and install packages
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
If PowerShell blocks activation, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then press `Ctrl + Shift + P`, choose **Python: Select Interpreter**, and pick the one inside `.venv`.

(macOS / Linux: `python3 -m venv .venv`, then `source .venv/bin/activate`.)

---

## 3. Connect MySQL (Server + Workbench)

### 3.1 Make sure the MySQL server is running
Press `Win + R`, type `services.msc`, find **MySQL80** (name may differ), and check that Status is **Running**. If not, right-click and Start.

### 3.2 Check the login in MySQL Workbench
1. Open Workbench and double-click your local connection (usually `Local instance MySQL80`, host `127.0.0.1`, port `3306`, user `root`).
2. Enter the root password you set during installation. If it opens, your credentials are correct.

### 3.3 Tell the project your login
Copy `.env.example` to `.env` (VS Code: right-click the file, Copy, Paste, rename) and fill in your details:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_real_password
DB_NAME=air_quality_db
```
Never share or upload `.env` (it is already in `.gitignore`).

### 3.4 Test the connection from Python
```powershell
python -m src.test_connection
```
You should see `Connected to MySQL 8.x ...`.

---

## 4. Get the data
1. On kaggle.com search **"Air Quality Data in India"** (dataset by Rohan Rao, 2015-2020) and download it.
2. Unzip it and copy **`city_day.csv`** into `data/raw/`.

> No Kaggle account yet? To test the setup first, run `python -m src.make_sample_data`
> and use `--file data/sample/city_day_sample.csv` in step 5.1. That file is **synthetic**:
> never use its numbers in your report.

---

## 5. Run the project

### 5.1 Clean the data
```powershell
python -m src.clean_data
```
Prints a missing-value report and saves `data/processed/city_day_clean.csv`.
(With the sample file: `python -m src.clean_data --file data/sample/city_day_sample.csv`)

### 5.2 Create the database and load the data
```powershell
python -m src.load_to_mysql
```
This runs `sql/01_schema.sql` (creates `air_quality_db`, tables `cities` and `air_readings`, and view `v_readings`) and loads the cleaned data. You can re-run it any time: it rebuilds the tables.

### 5.3 See it in MySQL Workbench
Click the refresh icon in the Schemas panel, expand `air_quality_db`, then open a new SQL tab and try:
```sql
USE air_quality_db;
SELECT * FROM v_readings LIMIT 100;
```
Open `sql/02_queries.sql` in Workbench (`File > Open SQL Script`) and run each query for your report screenshots.
Run `sql/03_dml_ddl_dcl_examples.sql` for the DDL / DML / DCL part (it cleans up after itself).

### 5.4 Start the dashboard
```powershell
streamlit run app/dashboard.py
```
It opens at `http://localhost:8501`. Stop it with `Ctrl + C` in the terminal.

---

## 6. Dashboard tabs
| Tab | What it shows |
|---|---|
| Overview | KPIs, city ranking, AQI category share, map of average AQI |
| Trends | Monthly line chart, year-wise bars, city x year heatmap |
| Seasonal & Outliers | City x season heatmap, box plots, IQR outlier table |
| Pollutants | Correlation matrix, pollutant vs AQI scatter |
| Lockdown 2020 | 25 Mar - 30 Apr, 2019 vs 2020 comparison |
| SQL Explorer | Shows and runs the 11 queries from `sql/02_queries.sql` live on MySQL |

The sidebar filters (cities, years, seasons, measure) apply to the charts.

---

## 7. Excel part of the project (Unit 1)
Open `data/raw/city_day.csv` in Excel and do the following on a copy:
1. **Missing values:** `=COUNTBLANK(range)` per column; decide to delete or leave blank and note it.
2. **Season column:** `=IF(OR(MONTH(B2)=12,MONTH(B2)<=2),"Winter",IF(MONTH(B2)<=5,"Summer",IF(MONTH(B2)<=9,"Monsoon","Post-monsoon")))`
3. **AQI category:** `=IFERROR(IF(O2<=50,"Good",IF(O2<=100,"Satisfactory",IF(O2<=200,"Moderate",IF(O2<=300,"Poor",IF(O2<=400,"Very Poor","Severe"))))),"")`
4. **Formulas:** `AVERAGEIF` (city average), `COUNTIF` (Poor days), `SUMIF`.
5. **Pivot tables:** City x Season average PM2.5; Year x City average AQI.
6. **Outliers:** `=QUARTILE(range,1)`, `=QUARTILE(range,3)`, fence = Q3 + 1.5 x (Q3 - Q1); highlight with Conditional Formatting.
7. **Distribution:** compare `AVERAGE` and `MEDIAN` of PM2.5 and explain the skew.

(Adjust the column letters to match your sheet.)

---

## 8. Troubleshooting
| Problem | Fix |
|---|---|
| `Can't connect to MySQL server on 'localhost'` | Start the **MySQL80** service (section 3.1); check `DB_PORT` |
| `Access denied for user 'root'` | Wrong password in `.env`. Test the same password in Workbench |
| `RuntimeError: 'cryptography' package is required` | `pip install cryptography` (it is in requirements.txt) |
| `Unknown database` / `Table doesn't exist` | Run `python -m src.load_to_mysql` |
| `streamlit` is not recognized | Activate the venv first: `.venv\Scripts\activate` |
| `ModuleNotFoundError: No module named 'src'` | Run commands from the project root folder, with `python -m src.<name>` |
| Password contains `@` or `#` | Fine: the code builds the URL safely, just put it in `.env` as is |
| Charts empty | Widen the sidebar filters (cities, years, seasons) |

---

## 9. Suggested report outline
1. Problem statement and objectives
2. Dataset description (columns, size, source)
3. Data cleaning (missing-value table, decisions) - Excel + `clean_data.py`
4. Database design (ER diagram: `cities` 1 - N `air_readings`, view `v_readings`) - screenshot from Workbench: *Database > Reverse Engineer*
5. SQL analysis (queries + output screenshots, DDL / DML / DCL)
6. Dashboard (screenshot of each tab) and key findings
7. Conclusion, limitations (missing data, unequal station coverage, no data after 2020), future work (forecasting with Prophet)
