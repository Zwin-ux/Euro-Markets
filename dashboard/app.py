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
GREEN = "#9EF3B8"
GREEN_DIM = "#5ECF82"
AMBER = "#F5C56B"
RED = "#FF8F70"
TEXT = "#EAF4E5"
MUTED = "#9FB8A4"
GRID = "rgba(158, 243, 184, 0.06)"


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Rajdhani:wght@500;600;700&display=swap');
        html, body, [class*="css"] { font-family: "IBM Plex Mono", monospace; color: #eaf4e5; }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(158,243,184,.10), transparent 24%),
                radial-gradient(circle at top right, rgba(245,197,107,.08), transparent 22%),
                linear-gradient(180deg, #040c08, #07120b),
                repeating-linear-gradient(0deg, rgba(158,243,184,.025) 0, rgba(158,243,184,.025) 1px, transparent 1px, transparent 28px),
                repeating-linear-gradient(90deg, rgba(158,243,184,.025) 0, rgba(158,243,184,.025) 1px, transparent 1px, transparent 38px);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,17,11,.98), rgba(7,15,10,.98));
            border-right: 1px solid rgba(158,243,184,.18);
        }
        [data-testid="stMetric"], .shell, .section, .note {
            border-radius: 18px;
            border: 1px solid rgba(158,243,184,.22);
            background: rgba(10,20,14,.80);
            box-shadow: inset 0 0 0 1px rgba(158,243,184,.04), 0 18px 40px rgba(0,0,0,.20);
        }
        [data-testid="stMetric"] { padding: .9rem 1rem; }
        [data-testid="stMetricLabel"] {
            color: #9fb8a4;
            text-transform: uppercase;
            letter-spacing: .16em;
            font-size: .68rem;
        }
        [data-testid="stMetricValue"] {
            color: #eaf4e5;
            font-family: "Rajdhani", sans-serif;
            font-weight: 700;
        }
        .shell {
            padding: 1.4rem 1.5rem;
            margin-bottom: 1rem;
            background:
                radial-gradient(circle at top right, rgba(245,197,107,.14), transparent 24%),
                linear-gradient(135deg, rgba(8,18,12,.98), rgba(11,27,17,.92));
        }
        .pills { display: flex; flex-wrap: wrap; gap: .45rem; margin-bottom: .9rem; }
        .pill {
            border: 1px solid rgba(158,243,184,.22);
            border-radius: 999px;
            padding: .24rem .65rem;
            color: #9ef3b8;
            background: rgba(10,20,14,.8);
            text-transform: uppercase;
            letter-spacing: .16em;
            font-size: .74rem;
        }
        .pill.amber { color: #f5c56b; border-color: rgba(245,197,107,.28); }
        .hero-grid { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr); gap: 1rem; }
        .hero-copy h1, .section h2, .sidebar-shell h2 {
            margin: 0;
            font-family: "Rajdhani", sans-serif;
            text-transform: uppercase;
            letter-spacing: .08em;
            color: #eaf4e5;
        }
        .hero-copy h1 { font-size: 2.65rem; line-height: .95; }
        .hero-copy p, .section p, .sidebar-shell p { color: #9fb8a4; line-height: 1.55; }
        .signal-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; }
        .signal {
            border-radius: 14px;
            border: 1px solid rgba(158,243,184,.18);
            background: rgba(11,23,16,.86);
            padding: .8rem .9rem;
        }
        .signal span, .eyebrow {
            color: #9ef3b8;
            font-size: .74rem;
            letter-spacing: .18em;
            text-transform: uppercase;
        }
        .signal strong {
            display: block;
            margin-top: .35rem;
            color: #eaf4e5;
            font-family: "Rajdhani", sans-serif;
            font-size: 1.4rem;
        }
        .section, .note, .sidebar-shell { padding: .95rem 1rem; margin: .4rem 0 .9rem; }
        .section h2 { font-size: 1.55rem; }
        .sidebar-shell { margin-bottom: 1rem; }
        .note { color: #f5c56b; border-color: rgba(245,197,107,.22); background: rgba(44,29,10,.32); }
        .upload-card {
            margin-top: .8rem;
            padding: .8rem .9rem;
            border-radius: 16px;
            border: 1px solid rgba(158,243,184,.22);
            background: rgba(10,20,14,.76);
        }
        .upload-card span { color: #9fb8a4; font-size: .74rem; text-transform: uppercase; letter-spacing: .16em; }
        .upload-card strong { display: block; margin-top: .3rem; font-family: "Rajdhani", sans-serif; font-size: 1.1rem; color: #eaf4e5; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 14px; border: 1px solid rgba(158,243,184,.18); background: rgba(9,18,12,.8);
            color: #9fb8a4; font-family: "Rajdhani", sans-serif; letter-spacing: .14em; text-transform: uppercase;
        }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, rgba(158,243,184,.16), rgba(245,197,107,.14)); color: #eaf4e5; }
        .stButton > button, .stDownloadButton > button {
            border-radius: 14px; border: 1px solid rgba(158,243,184,.28); background: linear-gradient(135deg, rgba(18,41,28,.96), rgba(13,28,19,.96));
            color: #eaf4e5; font-family: "Rajdhani", sans-serif; letter-spacing: .12em; text-transform: uppercase;
        }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div,
        [data-testid="stFileUploaderDropzone"], [data-testid="stDataFrame"], [data-testid="stDataEditor"], .stCodeBlock, pre {
            border-radius: 16px !important; border-color: rgba(158,243,184,.18) !important; background: rgba(10,20,14,.76) !important;
        }
        @media (max-width: 900px) { .hero-grid, .signal-grid { grid-template-columns: 1fr; } .hero-copy h1 { font-size: 2.1rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_percent(value: float, decimals: int = 2) -> str:
    return f"{value * 100:.{decimals}f}%"


def format_eur(value: float, decimals: int = 0, signed: bool = False) -> str:
    prefix = "+" if signed else ""
    return f"{prefix}{value:,.{decimals}f} EUR"


def section(title: str, kicker: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section">
            <div class="eyebrow">{kicker}</div>
            <h2>{title}</h2>
            <p>{description}</p>
        </div>
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


def style_chart(chart: alt.Chart, height: int = 320) -> alt.Chart:
    return (
        chart.properties(height=height)
        .configure(background="transparent")
        .configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor=MUTED,
            titleColor=MUTED,
            gridColor=GRID,
            domainColor="rgba(158, 243, 184, 0.18)",
            tickColor="rgba(158, 243, 184, 0.18)",
            labelFont="IBM Plex Mono",
            titleFont="IBM Plex Mono",
        )
        .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFont="IBM Plex Mono", titleFont="IBM Plex Mono")
        .configure_title(color=TEXT, font="Rajdhani", fontSize=18, anchor="start")
    )


def line_chart(frame: pd.DataFrame, x: str, y: str, color: str, title: str) -> alt.Chart:
    return style_chart(
        alt.Chart(frame)
        .mark_line(point=alt.OverlayMarkDef(size=54, filled=True), strokeWidth=2.6, color=color)
        .encode(x=alt.X(x, title="Date"), y=alt.Y(y, title=title), tooltip=list(frame.columns))
        .properties(title=title)
    )


def bar_chart(frame: pd.DataFrame, x: str, y: str, color: str, title: str, directional: bool = False) -> alt.Chart:
    return style_chart(
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color=color)
        .encode(
            x=alt.X(x, sort="-y", title=""),
            y=alt.Y(y, title=title),
            color=(
                alt.condition(f"datum.{y.split(':')[0]} >= 0", alt.value(GREEN), alt.value(RED))
                if directional
                else alt.value(color)
            ),
            tooltip=list(frame.columns),
        )
        .properties(title=title)
    )


def build_heatmap_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame({"row": [], "column": [], "value": []})
    matrix = frame.copy()
    matrix.index = matrix.index.map(str)
    matrix.columns = matrix.columns.map(str)
    matrix = matrix.rename_axis("row")
    return matrix.reset_index().melt(id_vars="row", var_name="column", value_name="value")


def heatmap_chart(frame: pd.DataFrame) -> alt.Chart:
    melted = build_heatmap_frame(frame)
    if melted.empty:
        return style_chart(alt.Chart(melted).mark_rect(), height=220)
    base = alt.Chart(melted)
    return style_chart(
        (
            base.mark_rect(cornerRadius=4).encode(
                x=alt.X("column:N", title=""),
                y=alt.Y("row:N", title=""),
                color=alt.Color("value:Q", scale=alt.Scale(domain=[-1, 1], range=["#7D2E2E", "#0D1710", GREEN]), title="Correlation"),
                tooltip=["row", "column", alt.Tooltip("value:Q", format=".3f")],
            )
            + base.mark_text(font="IBM Plex Mono", fontSize=11, color=TEXT).encode(text=alt.Text("value:Q", format=".2f"))
        ).properties(title="Cross-currency correlation"),
        height=max(220, 42 * max(len(frame.index), 1)),
    )


def load_portfolio_input(uploaded_file) -> tuple[pd.DataFrame, str]:
    if uploaded_file is None:
        return get_sample_portfolio_frame(), "Sample portfolio loaded from the local mission pack."
    return pd.read_csv(uploaded_file), "Custom portfolio uploaded and staged for analysis."


def render_hero(market_result: dict, focus_currency: str, portfolio_frame: pd.DataFrame) -> None:
    snapshot = market_result["latest_snapshot"]
    last_rate_date = snapshot["rate_date"].max() if not snapshot.empty else "Unavailable"
    coverage_count = int(snapshot["target_currency"].nunique()) if not snapshot.empty else 0
    st.markdown(
        f"""
        <div class="shell">
            <div class="pills">
                <span class="pill">ECB feed online</span>
                <span class="pill">railway deployed</span>
                <span class="pill amber">reporting currency {REPORTING_CURRENCY}</span>
            </div>
            <div class="hero-grid">
                <div class="hero-copy">
                    <h1>Capital Risk Intelligence</h1>
                    <p>
                        Tactical FX surveillance for EUR portfolios. Inspect live rate posture, exposure,
                        VaR, and stress scenarios from one terminal-style operating screen.
                    </p>
                </div>
                <div class="signal-grid">
                    <div class="signal"><span>Focus pair</span><strong>EUR/{focus_currency}</strong></div>
                    <div class="signal"><span>Snapshot coverage</span><strong>{coverage_count} FX legs</strong></div>
                    <div class="signal"><span>Portfolio rows</span><strong>{len(portfolio_frame):,}</strong></div>
                    <div class="signal"><span>Latest rate date</span><strong>{last_rate_date}</strong></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_tab(market_result: dict) -> None:
    section(
        "Market Radar",
        "live rate surveillance",
        "Monitor the active EUR cross, rate path, and realized volatility from the ECB-backed feed.",
    )
    summary = market_result["summary"]
    history = market_result["history"]
    latest_snapshot = market_result["latest_snapshot"]
    rolling_volatility = market_result["rolling_volatility"]

    metrics = st.columns(4)
    metrics[0].metric("Latest Rate", f"{summary['latest_rate']:.4f}")
    metrics[1].metric("Period Return", format_percent(summary["period_return"]))
    metrics[2].metric("Annualized Volatility", format_percent(summary["annualized_volatility"]))
    metrics[3].metric("Max Drawdown", format_percent(summary["max_drawdown"]))

    charts = st.columns((1.25, 1))
    with charts[0]:
        st.altair_chart(
            line_chart(history, "rate_date:T", "exchange_rate:Q", GREEN, "EUR cross history"),
            use_container_width=True,
        )
    with charts[1]:
        st.altair_chart(
            line_chart(rolling_volatility, "rate_date:T", "rolling_volatility:Q", AMBER, "Rolling volatility"),
            use_container_width=True,
        )

    section(
        "Snapshot Board",
        "current market posture",
        "Latest multi-currency ECB reference snapshot used by both the dashboard and the portfolio engine.",
    )
    st.dataframe(latest_snapshot, use_container_width=True, hide_index=True)


def render_portfolio_tab(
    portfolio_frame: pd.DataFrame,
    portfolio_message: str,
    lookback_days: int,
    confidence_level: float,
    rolling_window: int,
    frequency: str,
) -> None:
    section(
        "Portfolio Command",
        "risk operating picture",
        "Filter the book, inject bespoke currency shocks, and inspect exposure, VaR, and correlation from one panel.",
    )
    st.markdown(f"<div class='note'><strong>Portfolio source:</strong> {portfolio_message}</div>", unsafe_allow_html=True)

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
    section(
        "Scenario Overrides",
        "manual stress inputs",
        "Set shock percentages by currency. Positive values imply EUR strengthens against the target leg.",
    )
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

    analysis = get_portfolio_analysis_result(
        portfolio_csv=filtered_positions.to_csv(index=False),
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

    metrics = st.columns(6)
    metrics[0].metric("Portfolio Value", format_eur(summary["portfolio_value_eur"]))
    metrics[1].metric("1D FX P&L", format_eur(summary["fx_pnl_1d_eur"], signed=True))
    metrics[2].metric(f"{int(confidence_level * 100)}% 1D VaR", format_eur(summary["historical_var_1d_eur"]))
    metrics[3].metric("Annualized Volatility", format_percent(summary["annualized_portfolio_volatility"]))
    metrics[4].metric("Non-EUR Share", format_percent(summary["non_eur_share"], decimals=1))
    metrics[5].metric("Scenario Total", format_eur(summary["scenario_total_pnl_eur"], signed=True))

    charts = st.columns(2)
    with charts[0]:
        st.altair_chart(
            bar_chart(exposure, "currency:N", "value_eur:Q", GREEN_DIM, "EUR exposure by currency"),
            use_container_width=True,
        )
    with charts[1]:
        st.altair_chart(
            bar_chart(scenario_analysis, "currency:N", "scenario_pnl_eur:Q", RED, "Scenario P&L response", directional=True),
            use_container_width=True,
        )

    history = st.columns(2)
    with history[0]:
        st.altair_chart(
            line_chart(value_history, "rate_date:T", "portfolio_value_eur:Q", GREEN, "Portfolio value path"),
            use_container_width=True,
        )
    with history[1]:
        st.altair_chart(
            line_chart(rolling_volatility, "rate_date:T", "rolling_volatility:Q", AMBER, "Rolling portfolio volatility"),
            use_container_width=True,
        )

    section(
        "Correlation Grid",
        "dependency scan",
        "Pairwise return correlation across non-EUR exposures in the selected portfolio slice.",
    )
    st.altair_chart(heatmap_chart(correlation_matrix), use_container_width=True)

    detail_tabs = st.tabs(["Exposure Ledger", "Scenario Ledger", "Position Book"])
    with detail_tabs[0]:
        st.dataframe(exposure, use_container_width=True, hide_index=True)
    with detail_tabs[1]:
        st.dataframe(scenario_analysis, use_container_width=True, hide_index=True)
    with detail_tabs[2]:
        st.dataframe(positions, use_container_width=True, hide_index=True)


def render_platform_tab() -> None:
    section(
        "System Surface",
        "deployment and API contract",
        "Operator notes for running the local stack, testing the API, and validating the CSV interface.",
    )
    st.code(
        """\
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r requirements.txt
.\\.venv\\Scripts\\python -m streamlit run dashboard\\app.py
.\\.venv\\Scripts\\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
""",
        language="powershell",
    )

    section(
        "API Surface",
        "backend routes",
        "Primary endpoints exposed by the FastAPI layer that powers the dashboard and external integrations.",
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"method": "GET", "path": "/health", "purpose": "Service health and source metadata"},
                {"method": "GET", "path": "/currencies", "purpose": "Supported ECB currency catalog"},
                {"method": "GET", "path": "/rates/latest", "purpose": "Current EUR exchange rates"},
                {"method": "GET", "path": "/rates/history", "purpose": "Historical EUR FX series"},
                {"method": "GET", "path": "/market-monitor", "purpose": "Market dashboard payload"},
                {"method": "POST", "path": "/portfolio/analyze", "purpose": "Portfolio FX risk analysis"},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    section(
        "Portfolio CSV Contract",
        "input schema",
        "Minimum fields required to upload a book into the portfolio risk engine.",
    )
    st.code(
        """\
position_id,position_name,asset_class,book,currency,market_value_local
EQ-USD-01,US Equity Sleeve,Equity,Global Macro,USD,250000
BOND-GBP-01,UK Gilts,Bonds,Macro Rates,GBP,180000
""",
        language="csv",
    )


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")
    apply_styles()

    currency_catalog = get_currency_catalog()
    currency_options = currency_catalog.loc[
        currency_catalog["symbol"] != REPORTING_CURRENCY, "symbol"
    ].sort_values().tolist()
    default_market_currencies = [currency for currency in get_default_target_currencies() if currency in currency_options]

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-shell">
                <div class="eyebrow">control stack</div>
                <h2>Mission Parameters</h2>
                <p>Tune the surveillance horizon, choose the focus pair, and upload a portfolio file before the system assembles the risk picture.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
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
        st.markdown(
            """
            <div class="upload-card">
                <span>Input contract</span>
                <strong>position_id, position_name, currency, market_value_local</strong>
            </div>
            """,
            unsafe_allow_html=True,
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

    render_hero(market_result, focus_currency=focus_currency, portfolio_frame=portfolio_frame)

    market_tab, portfolio_tab, platform_tab = st.tabs(["Market Radar", "Portfolio Command", "System Surface"])
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


if __name__ == "__main__":
    main()
