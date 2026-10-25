"""Air Quality Analysis of Indian Cities : Streamlit dashboard (data comes from MySQL).

Run from the project root:
    streamlit run app/dashboard.py
"""
import sys
from pathlib import Path

# make "import src..." work when Streamlit starts this file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from src import config
from src.db import get_engine, load_named_queries

st.set_page_config(page_title="Air Quality of Indian Cities", page_icon="🌫️", layout="wide")

BUCKET_ORDER = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
BUCKET_COLORS = {"Good": "#00B050", "Satisfactory": "#92D050", "Moderate": "#FFD700",
                 "Poor": "#FF9800", "Very Poor": "#F44336", "Severe": "#9B1C1C"}
SEASON_ORDER = ["Winter", "Summer", "Monsoon", "Post-monsoon"]
METRICS = {"AQI": "aqi", "PM2.5": "pm25", "PM10": "pm10", "NO2": "no2",
           "SO2": "so2", "CO": "co", "O3": "o3", "NH3": "nh3"}


# ------------------------------------------------------------------ data
@st.cache_resource
def engine():
    return get_engine()


@st.cache_data(ttl=600, show_spinner="Loading data from MySQL...")
def load_readings() -> pd.DataFrame:
    with engine().connect() as conn:
        df = pd.read_sql(text("SELECT * FROM v_readings"), conn)
    df["reading_date"] = pd.to_datetime(df["reading_date"])
    num_cols = [c for c in df.columns if c not in
                ("city_name", "reading_date", "season", "aqi_bucket")]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return df


@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    with engine().connect() as conn:
        return pd.read_sql(text(sql), conn)


def aqi_color_scale():
    return [(0.0, "#00B050"), (0.2, "#92D050"), (0.4, "#FFD700"),
            (0.6, "#FF9800"), (0.8, "#F44336"), (1.0, "#9B1C1C")]


# --------------------------------------------------------------- connect
try:
    data = load_readings()
except Exception as exc:  # noqa: BLE001
    st.error("Could not read data from MySQL.")
    st.code(str(exc))
    st.markdown(
        "**Checklist:** 1) MySQL service is running  2) `.env` has the right password  "
        "3) you ran `python -m src.load_to_mysql`"
    )
    st.stop()

if data.empty:
    st.warning("The database is connected but empty. Run `python -m src.load_to_mysql`.")
    st.stop()

# --------------------------------------------------------------- sidebar
st.sidebar.title("Filters")
all_cities = sorted(data["city_name"].unique())
cities = st.sidebar.multiselect("Cities", all_cities, default=all_cities,
                                help="Clear the box and pick a few cities for cleaner trend lines")
y_min, y_max = int(data["yr"].min()), int(data["yr"].max())
years = st.sidebar.slider("Years", y_min, y_max, (y_min, y_max))
seasons = st.sidebar.multiselect("Seasons", SEASON_ORDER, default=SEASON_ORDER)
metric_label = st.sidebar.selectbox("Measure for charts", list(METRICS), index=0)
metric = METRICS[metric_label]
st.sidebar.caption(f"Database: `{config.DB_NAME}` on `{config.DB_HOST}`")

df = data[data["city_name"].isin(cities)
          & data["yr"].between(*years)
          & data["season"].isin(seasons)]

st.title("🌫️ Air Quality Analysis of Indian Cities")
st.caption("Source: CPCB data (Kaggle: Air Quality Data in India, 2015-2020), stored in MySQL, "
           "visualised with Streamlit and Plotly.")

if df.empty:
    st.warning("No data for these filters. Widen the selection in the sidebar.")
    st.stop()

tabs = st.tabs(["Overview", "Trends", "Seasonal & Outliers", "Pollutants",
                "Lockdown 2020", "SQL Explorer"])

# ================================================================ OVERVIEW
with tabs[0]:
    city_avg = df.groupby("city_name", as_index=False)["aqi"].mean().sort_values("aqi", ascending=False)
    bad = df["aqi_bucket"].isin(["Poor", "Very Poor", "Severe"]).mean() * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Average AQI", f"{df['aqi'].mean():.0f}")
    k2.metric("Most polluted city", city_avg.iloc[0]["city_name"], f"AQI {city_avg.iloc[0]['aqi']:.0f}",
              delta_color="inverse")
    k3.metric("Cleanest city", city_avg.iloc[-1]["city_name"], f"AQI {city_avg.iloc[-1]['aqi']:.0f}",
              delta_color="off")
    k4.metric("Poor or worse days", f"{bad:.1f}%")

    left, right = st.columns([3, 2])
    with left:
        fig = px.bar(city_avg, x="aqi", y="city_name", orientation="h", color="aqi",
                     color_continuous_scale=aqi_color_scale(), range_color=(30, 220),
                     labels={"aqi": "Average AQI", "city_name": ""},
                     title="Average AQI by city")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
                          height=620)
        st.plotly_chart(fig)
    with right:
        dist = (df["aqi_bucket"].value_counts().reindex(BUCKET_ORDER).fillna(0).reset_index())
        dist.columns = ["AQI category", "days"]
        fig = px.pie(dist, names="AQI category", values="days", hole=0.45,
                     color="AQI category", color_discrete_map=BUCKET_COLORS,
                     category_orders={"AQI category": BUCKET_ORDER},
                     title="Share of days by AQI category")
        st.plotly_chart(fig)

    map_df = (df.dropna(subset=["latitude", "longitude"])
                .groupby(["city_name", "latitude", "longitude"], as_index=False)["aqi"].mean())
    if not map_df.empty:
        fig = px.scatter_geo(map_df, lat="latitude", lon="longitude", color="aqi", size="aqi",
                             hover_name="city_name", hover_data={"aqi": ":.0f", "latitude": False,
                                                                 "longitude": False},
                             color_continuous_scale=aqi_color_scale(), range_color=(30, 220),
                             size_max=28, title="Average AQI map")
        fig.update_geos(fitbounds="locations", showcountries=True, countrycolor="#999",
                        showland=True, landcolor="#f2f2f2", showocean=True, oceancolor="#e8f1fa")
        fig.update_layout(height=560, margin={"l": 0, "r": 0, "t": 50, "b": 0})
        st.plotly_chart(fig)

# ================================================================== TRENDS
with tabs[1]:
    st.subheader(f"{metric_label} over time")
    monthly = (df.groupby([pd.Grouper(key="reading_date", freq="MS"), "city_name"])[metric]
                 .mean().reset_index())
    fig = px.line(monthly, x="reading_date", y=metric, color="city_name",
                  labels={"reading_date": "Month", metric: f"Monthly average {metric_label}",
                          "city_name": "City"})
    fig.update_layout(height=480)
    st.plotly_chart(fig)

    c1, c2 = st.columns(2)
    with c1:
        yearly = df.groupby("yr", as_index=False)[metric].mean()
        fig = px.bar(yearly, x="yr", y=metric, text_auto=".0f",
                     labels={"yr": "Year", metric: f"Average {metric_label}"},
                     title=f"Year-wise average {metric_label} (selected cities)")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig)
    with c2:
        heat = df.pivot_table(index="city_name", columns="yr", values=metric, aggfunc="mean")
        fig = px.imshow(heat, aspect="auto", text_auto=".0f", color_continuous_scale="YlOrRd",
                        labels={"color": metric_label, "x": "Year", "y": ""},
                        title=f"City x Year heatmap of {metric_label}")
        st.plotly_chart(fig)

# ======================================================= SEASONAL & OUTLIERS
with tabs[2]:
    st.subheader(f"Seasonal pattern of {metric_label}")
    c1, c2 = st.columns(2)
    with c1:
        heat = (df.pivot_table(index="city_name", columns="season", values=metric, aggfunc="mean")
                  .reindex(columns=[s for s in SEASON_ORDER if s in df["season"].unique()]))
        fig = px.imshow(heat, aspect="auto", text_auto=".0f", color_continuous_scale="YlOrRd",
                        labels={"color": metric_label, "x": "", "y": ""},
                        title="City x Season (average)")
        fig.update_layout(height=620)
        st.plotly_chart(fig)
    with c2:
        fig = px.box(df, x="season", y=metric, color="season",
                     category_orders={"season": SEASON_ORDER},
                     labels={metric: metric_label, "season": ""},
                     title="Distribution by season (dots = outliers)")
        fig.update_layout(showlegend=False, height=620)
        st.plotly_chart(fig)

    st.subheader(f"Outlier detection for {metric_label} (IQR method)")
    st.caption("A reading is an outlier when it is above Q3 + 1.5 x IQR of its own city. "
               "This mirrors the Excel outlier step of your project.")
    q = df.groupby("city_name")[metric].quantile([0.25, 0.75]).unstack()
    q.columns = ["Q1", "Q3"]
    q["IQR"] = q["Q3"] - q["Q1"]
    q["upper_fence"] = q["Q3"] + 1.5 * q["IQR"]
    tmp = df.join(q["upper_fence"], on="city_name")
    out = tmp[tmp[metric] > tmp["upper_fence"]].groupby("city_name")[metric].agg(
        outliers="count", highest="max")
    summary = q.join(out).fillna({"outliers": 0}).round(1).sort_values("outliers", ascending=False)
    summary["outliers"] = summary["outliers"].astype(int)
    st.dataframe(summary)

# ============================================================== POLLUTANTS
with tabs[3]:
    st.subheader("How do pollutants relate to AQI?")
    pol_cols = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3", "aqi"]
    corr = df[pol_cols].corr().round(2)
    corr.index = corr.columns = [c.upper().replace("PM25", "PM2.5") for c in corr.columns]
    c1, c2 = st.columns(2)
    with c1:
        fig = px.imshow(corr, text_auto=True, zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                        title="Correlation matrix")
        fig.update_layout(height=520)
        st.plotly_chart(fig)
    with c2:
        x_label = st.selectbox("Pollutant on X axis", [m for m in METRICS if m != "AQI"], index=0)
        sample = df[[METRICS[x_label], "aqi", "city_name"]].dropna()
        sample = sample.sample(min(len(sample), 5000), random_state=1)
        fig = px.scatter(sample, x=METRICS[x_label], y="aqi", color="city_name", opacity=0.6,
                         labels={METRICS[x_label]: x_label, "aqi": "AQI"},
                         title=f"{x_label} vs AQI (random sample of up to 5,000 days)")
        fig.update_layout(height=470)
        st.plotly_chart(fig)
    st.info("A correlation close to +1 means the pollutant rises together with AQI. "
            "In the CPCB method, AQI is decided by the worst sub-index, so PM2.5 and PM10 "
            "usually show the strongest link in this data.")

# =========================================================== LOCKDOWN 2020
with tabs[4]:
    st.subheader("Did the COVID-19 lockdown clean the air?")
    st.caption("Compares 25 March to 30 April of 2019 and 2020 (uses all cities and the measure "
               "chosen in the sidebar; year and season filters are ignored on this tab).")
    base = data[data["city_name"].isin(cities)]
    in_window = (base["reading_date"].dt.month.isin([3, 4])
                 & (((base["reading_date"].dt.month == 3) & (base["reading_date"].dt.day >= 25))
                    | ((base["reading_date"].dt.month == 4))))
    win = base[in_window & base["yr"].isin([2019, 2020])]
    comp = win.pivot_table(index="city_name", columns="yr", values=metric, aggfunc="mean").dropna()
    if comp.empty or 2019 not in comp.columns or 2020 not in comp.columns:
        st.warning("Not enough data for 2019 and 2020 in the selected cities.")
    else:
        comp["change_pct"] = ((comp[2020] - comp[2019]) / comp[2019] * 100).round(1)
        comp = comp.sort_values("change_pct")
        long = comp.reset_index().melt(id_vars="city_name", value_vars=[2019, 2020],
                                       var_name="Year", value_name=metric_label)
        long["Year"] = long["Year"].astype(str)
        fig = px.bar(long, x="city_name", y=metric_label, color="Year", barmode="group",
                     color_discrete_map={"2019": "#4C78A8", "2020": "#F58518"},
                     labels={"city_name": ""}, title=f"Average {metric_label}: 25 Mar - 30 Apr")
        st.plotly_chart(fig)
        m1, m2 = st.columns(2)
        m1.metric("Average change across cities", f"{comp['change_pct'].mean():.1f}%")
        m2.metric("Cities with lower pollution in 2020", f"{(comp['change_pct'] < 0).sum()} of {len(comp)}")
        st.dataframe(comp.rename(columns={2019: "2019", 2020: "2020"}).round(1))

# ============================================================ SQL EXPLORER
with tabs[5]:
    st.subheader("SQL queries run on MySQL")
    st.caption("These come from `sql/02_queries.sql`. Pick one, read the SQL, and run it live.")
    queries = load_named_queries(config.SQL_DIR / "02_queries.sql")
    titles = {q["title"]: q for q in queries}
    choice = st.selectbox("Query", list(titles))
    q = titles[choice]
    st.markdown(f"**Concepts used:** {q['concept']}")
    st.code(q["sql"] + ";", language="sql")
    if st.button("Run query", type="primary"):
        try:
            result = run_query(q["sql"])
            st.dataframe(result, hide_index=True)
            st.download_button("Download result as CSV", result.to_csv(index=False).encode(),
                               file_name=f"{q['name']}.csv", mime="text/csv")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    with st.expander("Browse the raw table (first 1,000 filtered rows)"):
        st.dataframe(df.sort_values("reading_date").head(1000), hide_index=True)
