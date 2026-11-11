"""Streamlit dashboard: Murray-Darling water allocation market (2001-2027).

Run locally with:  streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import statsmodels.formula.api as smf
import streamlit as st

st.set_page_config(page_title="Murray-Darling water market", layout="wide")

FORMULA = "log_P ~ a_High + a_Low + np.log(R) + carry_share + {period} + C(Region)"
REPO = "https://github.com/imadramdani-prog/murray-darling-water-market"


# ---------- data and models ----------
@st.cache_data
def load_data():
    panel = pd.read_csv("data/processed/panel_2001_2027.csv")
    scen = pd.read_csv("data/processed/forecast_scenario_a.csv")
    return panel, scen


@st.cache_resource
def fit_models(panel):
    data = panel[panel["Year"] <= 2026].copy()
    data["p2017_21"] = data["Year"].between(2017, 2021).astype(int)
    data["p2022_26"] = (data["Year"] >= 2022).astype(int)
    clustered = {"cov_type": "cluster", "cov_kwds": {"groups": data["Year"]}}

    periods = smf.ols(FORMULA.format(period="p2017_21 + p2022_26"), data=data).fit(**clustered)
    main = smf.ols(FORMULA.format(period="after_2016"), data=data).fit(**clustered)

    train = data[data["Year"] <= 2016]
    oos = smf.ols("log_P ~ a_High + a_Low + np.log(R) + carry_share + C(Region)", data=train).fit()
    return data, periods, main, oos


panel, scen = load_data()
data, periods, main, oos = fit_models(panel)
smearing = np.exp(main.resid).mean()


def premium(name):
    return np.exp(periods.params[name]) - 1


# ---------- header ----------
st.title("Water as a financial asset: the Murray-Darling allocation market")
st.markdown(
    "Allocation prices in the southern Murray-Darling Basin, 2001-2027. "
    "Data: ABARES (2001-2021), extended to 2026 with Bureau of Meteorology trade records, "
    "state allocation announcements and SILO rainfall. Prices in 2019-20 dollars. "
    f"Code and method: [GitHub]({REPO})."
)

actual_2027 = panel[panel["Year"] == 2027]["P"].mean()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Premium 2017-21 vs 2001-16", f"+{premium('p2017_21'):.0%}")
c2.metric("Premium 2022-26 vs 2001-16", f"+{premium('p2022_26'):.0%}")
c3.metric("Average price 2025-26", f"${data[data['Year'] == 2026]['P'].mean():.0f}/ML")
c4.metric("Actual Aug-Nov 2026", f"${actual_2027:.0f}/ML")
st.caption(
    "Premium = how much higher prices were than in 2001-16 at comparable allocations, "
    "rainfall and carryover (panel regression with region fixed effects, year-clustered errors)."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Price history", "Fundamentals vs actual", "Forecast 2026-28", "Price simulator"]
)

# ---------- tab 1: price history ----------
with tab1:
    regions = sorted(panel["Region"].unique())
    chosen = st.multiselect("Regions", regions, default=["VIC Murray Below", "NSW Murrumbidgee"])
    hist = panel[panel["Year"] <= 2026]
    fig = go.Figure()
    basin = hist.groupby("Year")["P"].mean()
    fig.add_trace(go.Scatter(x=basin.index, y=basin.values, name="Southern basin average",
                             line=dict(color="black", width=3)))
    for region in chosen:
        r = hist[hist["Region"] == region]
        fig.add_trace(go.Scatter(x=r["Year"], y=r["P"], name=region, mode="lines+markers"))
    fig.add_vline(x=2021.5, line_dash="dot", line_color="grey",
                  annotation_text="ABARES | BOM extension", annotation_position="top")
    fig.update_layout(yaxis_title="Price ($/ML, 2019-20 dollars)", xaxis_title="Water year (ending June)",
                      height=480, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")

# ---------- tab 2: out-of-sample ----------
with tab2:
    test = data[data["Year"] >= 2017].copy()
    test["pred_P"] = np.exp(oos.predict(test)) * np.exp(oos.resid).mean()
    by_year = test.groupby("Year")[["P", "pred_P"]].mean()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=by_year.index, y=by_year["P"], name="Actual"))
    fig.add_trace(go.Bar(x=by_year.index, y=by_year["pred_P"], name="Predicted from 2001-16 fundamentals"))
    fig.update_layout(barmode="group", height=480, yaxis_title="Price ($/ML, 2019-20 dollars)",
                      xaxis_title="Water year (ending June)", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    gap = np.exp((np.log(by_year["P"]) - np.log(by_year["pred_P"])).mean()) - 1
    st.markdown(
        f"A model trained only on 2001-2016 underpredicts every year since 2017 "
        f"(average gap: **+{gap:.0%}**). The premium held in the wet years 2022-24 and the dry years 2025-26."
    )

# ---------- tab 3: forecast ----------
with tab3:
    summary = scen.groupby(["Year", "scenario"])["pred_P"].mean().unstack()
    start = data[data["Year"] == 2026]["P"].mean()
    recent = data[data["Year"] >= 2015].groupby("Year")["P"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent.index, y=recent.values, name="Actual price",
                             line=dict(color="black"), mode="lines+markers"))
    colors = {"dry": "#d62728", "average": "#1f77b4", "wet": "#2ca02c"}
    for name in ["dry", "average", "wet"]:
        fig.add_trace(go.Scatter(x=[2026, 2027, 2028], y=[start, *summary[name]],
                                 name=f"Scenario A, {name} year", mode="lines+markers",
                                 line=dict(color=colors[name], dash="dash")))
    fig.add_trace(go.Scatter(x=[2027], y=[actual_2027], name="Actual Aug-Nov 2026 (partial year)",
                             mode="markers", marker=dict(symbol="diamond", size=14, color="gold",
                                                         line=dict(color="black", width=1))))
    fig.add_vline(x=2026.5, line_dash="dot", line_color="grey", annotation_text="Jul 2026: anti-manipulation rules",
                  annotation_position="top left")
    fig.add_vline(x=2027.5, line_dash="dot", line_color="grey", annotation_text="Jul 2027: data obligations",
                  annotation_position="bottom right")
    fig.update_layout(height=480, yaxis_title="Price ($/ML, 2019-20 dollars)",
                      xaxis_title="Water year (ending June)", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    table = summary[["dry", "average", "wet"]].round(0)
    table.index = ["2026-27", "2027-28"]
    st.dataframe(table.style.format("${:.0f}"), width="content")
    st.markdown(
        "Scenario A: model trained on data up to June 2026, before the new market rules, assuming the "
        "post-2016 premium continues. Dry, average and wet years use each region's 10th, 50th and 90th "
        "percentile of rainfall and allocations (2001-2026); 2026-27 allocations cannot fall below what "
        "has already been announced. Forecasts will be compared with actual prices as they are published."
    )

# ---------- tab 4: simulator ----------
with tab4:
    st.markdown("Choose supply conditions and see the price the model predicts.")
    col_a, col_b = st.columns(2)
    region = col_a.selectbox("Region", regions, index=regions.index("VIC Murray Below"))
    rr = data[data["Region"] == region]
    a_high = col_a.slider("High-reliability allocation (%)", 0, 100, 100) / 100
    a_low = col_a.slider("Low-reliability allocation (%)", 0, 100, 0) / 100
    rain = col_b.slider("Rainfall, August to May (mm)", int(rr["R"].min()), int(rr["R"].max()),
                        int(rr["R"].median()))
    carry = col_b.slider("Carryover (% of entitlements)", 0, 80, int(rr["carry_share"].median() * 100)) / 100
    post = col_b.toggle("Post-2016 market (premium on)", value=True)

    x = pd.DataFrame({"Region": [region], "a_High": [a_high], "a_Low": [a_low], "R": [rain],
                      "carry_share": [carry], "after_2016": [int(post)]})
    price = float(np.exp(main.predict(x).iloc[0]) * smearing)
    st.metric("Predicted allocation price", f"${price:.0f}/ML (2019-20 dollars)")
    st.caption("Model: panel regression on 2001-2026 with region fixed effects. "
               "Illustrative only: it does not include demand shifts or market behaviour.")

# ---------- footer ----------
with st.expander("Data sources and limitations"):
    st.markdown(
        "- **Prices**: ABARES MDB Water Market Catchment Dataset (2001-2021); BOM allocation trades "
        "(volume-weighted monthly prices, August-May, deflated with the ABS CPI) from 2022. "
        "Overlap check 2009-2021: correlation 0.99, median gap -0.4%.\n"
        "- **Allocations and carryover**: WaterNSW WaterInsights, Northern Victoria Resource Manager, "
        "Victorian Water Accounts, Goulburn-Murray Water, SA Department for Environment and Water.\n"
        "- **Rainfall**: SILO (Queensland Government), one representative town per region, scaled to ABARES.\n"
        "- **Limitations**: environmental share and entitlements held at 2020-21 levels; some carryover "
        "values estimated; 2026-27 is a partial year; the model shows that the premium persists, not why."
    )
