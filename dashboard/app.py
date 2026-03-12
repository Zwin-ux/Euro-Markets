from __future__ import annotations

import io
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.portfolio_risk import clean_portfolio_positions
from services.market_service import (
    build_market_monitor,
    build_portfolio_analysis,
    get_default_target_currencies,
    get_supported_currency_catalog,
    load_sample_portfolio,
)

PAGE_TITLE = "Capital Risk Intelligence"
REPORTING_CURRENCY = "EUR"


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: "Space Grotesk", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(14, 165, 233, 0.18), transparent 32%),
                radial-gradient(circle at top right, rgba(251, 191, 36, 0.18), transparent 28%),
                linear-gradient(180deg, #f4f7fb 0%, #fbfcfe 100%);
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 0.8rem 1rem;
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
        }

        .hero {
            padding: 1.4rem 1.5rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(10, 37, 64, 0.96), rgba(7, 89, 133, 0.92));
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 16px 36px rgba(7, 89, 133, 0.24);
        }

        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
            letter-spacing: -0.04em;
        }

        .hero p {
            margin: 0.45rem 0 0 0;
            max-width: 52rem;
            color: rgba(255, 255, 255, 0.78);
        }

        .section-note {
            color: #475569;
            font-size: 0.94rem;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=3600)
def get_currency_catalog() -> pd.DataFrame:
    return get_supported_currency_catalog()


@st.cache_data(ttl=3600)
def get_sample_portfolio_frame() -> pd.DataFrame:
    return load_sample_portfolio()


@st.cache_data(ttl=900)
def get_market_monitor_result(
    focus_currency: str,
    currencies: tuple[str, ...],
    lookback_days: int,
    frequency: str,
) -> dict:
    return build_market_monitor(
        focus_currency=focus_currency,
        currencies=list(currencies),
        lookback_days=lookback_days,
        frequency=frequency,
    )


@st.cache_data(ttl=900)
def get_portfolio_analysis_result(
    portfolio_csv: str,
    lookback_days: int,
    confidence_level: float,
    rolling_window: int,
    frequency: str,
    scenario_shocks: tuple[tuple[str, float], ...],
) -> dict:
    positions = pd.read_csv(io.StringIO(portfolio_csv))
    return build_portfolio_analysis(
        positions=positions,
        lookback_days=lookback_days,
        confidence_level=confidence_level,
        rolling_window=rolling_window,
        frequency=frequency,
        scenario_shocks=dict(scenario_shocks),
    )


def line_chart(frame: pd.DataFrame, x: str, y: str, color: str, title: str) -> alt.Chart:
    return (
        alt.Chart(frame)
        .mark_line(point=True, strokeWidth=3, color=color)
        .encode(
            x=alt.X(x, title="Date"),
            y=alt.Y(y, title=title),
            tooltip=list(frame.columns),
        )
        .properties(height=300)
    )


def bar_chart(frame: pd.DataFrame, x: str, y: str, color: str, title: str) -> alt.Chart:
    return (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color=color)
        .encode(
            x=alt.X(x, sort="-y", title=""),
            y=alt.Y(y, title=title),
            tooltip=list(frame.columns),
        )
        .properties(height=300)
    )


def heatmap_chart(frame: pd.DataFrame) -> alt.Chart:
    if frame.empty:
        return alt.Chart(pd.DataFrame({"x": [], "y": [], "value": []})).mark_rect()

    melted = frame.reset_index().melt(id_vars="index", var_name="column", value_name="value")
    melted = melted.rename(columns={"index": "row"})
    return (
        alt.Chart(melted)
        .mark_rect(cornerRadius=6)
        .encode(
            x=alt.X("column:N", title=""),
            y=alt.Y("row:N", title=""),
            color=alt.Color("value:Q", scale=alt.Scale(scheme="tealblues"), title="Correlation"),
            tooltip=["row", "column", alt.Tooltip("value:Q", format=".3f")],
        )
        .properties(height=320)
    )


def load_portfolio_input(uploaded_file) -> tuple[pd.DataFrame, str]:
    if uploaded_file is None:
        return get_sample_portfolio_frame(), "Using the bundled sample portfolio."
    return pd.read_csv(uploaded_file), "Using your uploaded portfolio."


def render_market_tab(market_result: dict) -> None:
    summary = market_result["summary"]
    history = market_result["history"]
    latest_snapshot = market_result["latest_snapshot"]
    rolling_volatility = market_result["rolling_volatility"]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Latest Rate", f"{summary['latest_rate']:.4f}")
    metric_columns[1].metric("Period Return", f"{summary['period_return'] * 100:.2f}%")
    metric_columns[2].metric("Annualized Volatility", f"{summary['annualized_volatility'] * 100:.2f}%")
    metric_columns[3].metric("Max Drawdown", f"{summary['max_drawdown'] * 100:.2f}%")

    chart_columns = st.columns((1.3, 1))
    with chart_columns[0]:
        st.altair_chart(
            line_chart(history, "rate_date:T", "exchange_rate:Q", "#0f766e", "EUR FX history"),
            use_container_width=True,
        )
    with chart_columns[1]:
        st.altair_chart(
            line_chart(rolling_volatility, "rate_date:T", "rolling_volatility:Q", "#b45309", "Rolling volatility"),
            use_container_width=True,
        )

    st.subheader("Latest ECB Snapshot")
    st.dataframe(latest_snapshot, use_container_width=True, hide_index=True)


def render_portfolio_tab(
    portfolio_frame: pd.DataFrame,
    portfolio_message: str,
    lookback_days: int,
    confidence_level: float,
    rolling_window: int,
    frequency: str,
) -> None:
    st.markdown(f"<div class='section-note'>{portfolio_message}</div>", unsafe_allow_html=True)

    cleaned_positions = clean_portfolio_positions(portfolio_frame)
    filters = st.columns(2)
    selected_books = filters[0].multiselect(
        "Books",
        options=sorted(book for book in cleaned_positions["book"].unique() if book),
        default=sorted(book for book in cleaned_positions["book"].unique() if book),
    )
    selected_asset_classes = filters[1].multiselect(
        "Asset classes",
        options=sorted(asset_class for asset_class in cleaned_positions["asset_class"].unique() if asset_class),
        default=sorted(asset_class for asset_class in cleaned_positions["asset_class"].unique() if asset_class),
    )

    filtered_positions = cleaned_positions.copy()
    if selected_books:
        filtered_positions = filtered_positions[filtered_positions["book"].isin(selected_books)]
    if selected_asset_classes:
        filtered_positions = filtered_positions[filtered_positions["asset_class"].isin(selected_asset_classes)]

    if filtered_positions.empty:
        st.warning("No positions remain after the selected filters.")
        return

    scenario_base = pd.DataFrame(
        {
            "currency": [currency for currency in sorted(filtered_positions["currency"].unique()) if currency != REPORTING_CURRENCY],
            "shock_pct": 0.0,
        }
    )
    st.subheader("Scenario Shocks")
    st.caption("Enter rate shocks in percent. Positive values mean EUR strengthens against that currency.")
    scenario_editor = st.data_editor(
        scenario_base,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={"shock_pct": st.column_config.NumberColumn("Shock (%)", format="%.2f")},
    )
    scenario_shocks = tuple(
        (row["currency"], float(row["shock_pct"]) / 100.0)
        for _, row in scenario_editor.iterrows()
        if float(row["shock_pct"]) != 0.0
    )

    portfolio_csv = filtered_positions.to_csv(index=False)
    analysis = get_portfolio_analysis_result(
        portfolio_csv=portfolio_csv,
        lookback_days=lookback_days,
        confidence_level=confidence_level,
        rolling_window=rolling_window,
        frequency=frequency,
        scenario_shocks=scenario_shocks,
    )

    summary = analysis["summary"]
    exposure = analysis["currency_exposure"]
    value_history = analysis["portfolio_value_history"]
    rolling_volatility = analysis["rolling_volatility"]
    scenario_analysis = analysis["scenario_analysis"]
    correlation_matrix = analysis["correlation_matrix"]
    positions = analysis["positions"]

    metric_columns = st.columns(5)
    metric_columns[0].metric("Portfolio Value (EUR)", f"{summary['portfolio_value_eur']:,.0f}")
    metric_columns[1].metric("1D FX P&L", f"{summary['fx_pnl_1d_eur']:,.0f} EUR")
    metric_columns[2].metric(
        f"{int(confidence_level * 100)}% 1D VaR",
        f"{summary['historical_var_1d_eur']:,.0f} EUR",
    )
    metric_columns[3].metric(
        "Annualized Volatility",
        f"{summary['annualized_portfolio_volatility'] * 100:.2f}%",
    )
    metric_columns[4].metric("Non-EUR Share", f"{summary['non_eur_share'] * 100:.1f}%")

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.altair_chart(
            bar_chart(exposure, "currency:N", "value_eur:Q", "#0369a1", "EUR exposure"),
            use_container_width=True,
        )
    with chart_columns[1]:
        st.altair_chart(
            bar_chart(scenario_analysis, "currency:N", "scenario_pnl_eur:Q", "#be123c", "Scenario P&L"),
            use_container_width=True,
        )

    history_columns = st.columns(2)
    with history_columns[0]:
        st.altair_chart(
            line_chart(value_history, "rate_date:T", "portfolio_value_eur:Q", "#0f172a", "Portfolio value"),
            use_container_width=True,
        )
    with history_columns[1]:
        st.altair_chart(
            line_chart(rolling_volatility, "rate_date:T", "rolling_volatility:Q", "#c2410c", "Rolling volatility"),
            use_container_width=True,
        )

    st.subheader("Currency Correlation")
    st.altair_chart(heatmap_chart(correlation_matrix), use_container_width=True)

    detail_tabs = st.tabs(["Exposure", "Scenario", "Positions"])
    with detail_tabs[0]:
        st.dataframe(exposure, use_container_width=True, hide_index=True)
    with detail_tabs[1]:
        st.dataframe(scenario_analysis, use_container_width=True, hide_index=True)
    with detail_tabs[2]:
        st.dataframe(positions, use_container_width=True, hide_index=True)


def render_platform_tab() -> None:
    st.subheader("Run The Stack")
    st.code(
        """\
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r requirements.txt
.\\.venv\\Scripts\\python -m streamlit run dashboard\\app.py
.\\.venv\\Scripts\\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
""",
        language="powershell",
    )

    st.subheader("API Surface")
    api_catalog = pd.DataFrame(
        [
            {"method": "GET", "path": "/health", "purpose": "Service health and source metadata"},
            {"method": "GET", "path": "/currencies", "purpose": "Supported ECB currency catalog"},
            {"method": "GET", "path": "/rates/latest", "purpose": "Current EUR exchange rates"},
            {"method": "GET", "path": "/rates/history", "purpose": "Historical EUR FX series"},
            {"method": "GET", "path": "/market-monitor", "purpose": "Market dashboard payload"},
            {"method": "POST", "path": "/portfolio/analyze", "purpose": "Portfolio FX risk analysis"},
        ]
    )
    st.dataframe(api_catalog, use_container_width=True, hide_index=True)

    st.subheader("Portfolio CSV Contract")
    st.code(
        """\
position_id,position_name,asset_class,book,currency,market_value_local
EQ-USD-01,US Equity Sleeve,Equity,Global Macro,USD,250000
BOND-GBP-01,UK Gilts,Bonds,Macro Rates,GBP,180000
""",
        language="csv",
    )


st.set_page_config(page_title=PAGE_TITLE, layout="wide")
apply_styles()

st.markdown(
    """
    <div class="hero">
        <h1>Capital Risk Intelligence</h1>
        <p>
            ECB-backed foreign-exchange analytics for live market monitoring, portfolio exposure,
            value-at-risk, and stress scenarios.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

currency_catalog = get_currency_catalog()
currency_options = (
    currency_catalog.loc[currency_catalog["symbol"] != REPORTING_CURRENCY, "symbol"].sort_values().tolist()
)
default_market_currencies = [currency for currency in get_default_target_currencies() if currency in currency_options]

with st.sidebar:
    st.header("Controls")
    focus_currency = st.selectbox(
        "Focus currency",
        options=currency_options,
        index=currency_options.index("USD") if "USD" in currency_options else 0,
    )
    market_currencies = st.multiselect(
        "Market snapshot currencies",
        options=currency_options,
        default=default_market_currencies or currency_options[:6],
    )
    frequency = st.selectbox("Frequency", options=["D", "M", "Q", "A"], index=0)
    lookback_days = st.slider("Lookback window", min_value=30, max_value=365, value=180, step=30)
    confidence_level = st.slider("VaR confidence level", min_value=0.80, max_value=0.99, value=0.95, step=0.01)
    rolling_window = st.slider("Rolling volatility window", min_value=5, max_value=60, value=20, step=1)

    uploaded_portfolio = st.file_uploader("Upload portfolio CSV", type=["csv"])
    sample_portfolio = get_sample_portfolio_frame()
    st.download_button(
        "Download sample portfolio",
        data=sample_portfolio.to_csv(index=False),
        file_name="sample_portfolio.csv",
        mime="text/csv",
    )

try:
    market_result = get_market_monitor_result(
        focus_currency=focus_currency,
        currencies=tuple(market_currencies or default_market_currencies or currency_options[:6]),
        lookback_days=lookback_days,
        frequency=frequency,
    )
    portfolio_frame, portfolio_message = load_portfolio_input(uploaded_portfolio)
except Exception as exc:
    st.error(f"Unable to load ECB market data: {exc}")
    st.stop()

market_tab, portfolio_tab, platform_tab = st.tabs(["Market Radar", "Portfolio Lab", "Platform"])
with market_tab:
    render_market_tab(market_result)
with portfolio_tab:
    render_portfolio_tab(
        portfolio_frame=portfolio_frame,
        portfolio_message=portfolio_message,
        lookback_days=lookback_days,
        confidence_level=confidence_level,
        rolling_window=rolling_window,
        frequency=frequency,
    )
with platform_tab:
    render_platform_tab()
