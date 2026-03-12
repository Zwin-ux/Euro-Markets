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
                radial-gradient(circle at top left, rgba(158,243,184,.08), transparent 24%),
                linear-gradient(180deg, #050b08, #08110d);
        }
        .block-container { padding-top: 1rem; padding-bottom: 2.25rem; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,17,11,.98), rgba(8,15,11,.98));
            border-right: 1px solid rgba(158,243,184,.18);
        }
        .page-header, [data-testid="stMetric"], .table-shell {
            border-radius: 16px;
            border: 1px solid rgba(158,243,184,.22);
            background: rgba(10,20,14,.82);
        }
        .page-header {
            padding: 1.2rem 1.3rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, rgba(8,18,12,.98), rgba(10,23,16,.94));
        }
        .header-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: flex-start;
        }
        .status-line {
            display: flex;
            gap: .45rem;
            flex-wrap: wrap;
            margin-bottom: .8rem;
        }
        .status-chip {
            padding: .24rem .58rem;
            border-radius: 999px;
            border: 1px solid rgba(158,243,184,.22);
            color: #9ef3b8;
            background: rgba(8,18,12,.72);
            font-size: .72rem;
            letter-spacing: .14em;
            text-transform: uppercase;
        }
        .header-copy h1, .section-intro h2, .sidebar-shell h2 {
            margin: 0;
            font-family: "Rajdhani", sans-serif;
            color: #ecf6ea;
            letter-spacing: .04em;
        }
        .header-copy h1 { font-size: 2.35rem; line-height: .95; }
        .header-copy p, .section-intro p, .sidebar-shell p, .sidebar-note {
            color: #a8b5ac;
            line-height: 1.55;
        }
        .header-stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .7rem;
            min-width: min(360px, 100%);
        }
        .header-stat {
            padding: .75rem .85rem;
            border-radius: 14px;
            border: 1px solid rgba(158,243,184,.18);
            background: rgba(8,18,12,.64);
        }
        .header-stat span {
            display: block;
            color: #9fb8a4;
            font-size: .72rem;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        .header-stat strong {
            display: block;
            margin-top: .3rem;
            color: #ecf6ea;
            font-family: "Rajdhani", sans-serif;
            font-size: 1.35rem;
        }
        .section-intro { margin: .1rem 0 .8rem 0; }
        .section-intro h2 { font-size: 1.55rem; }
        .section-intro p { margin: .32rem 0 0 0; max-width: 52rem; }
        [data-testid="stMetric"] { padding: .85rem .95rem; }
        [data-testid="stMetricLabel"] {
            color: #90a493;
            text-transform: uppercase;
            letter-spacing: .12em;
            font-size: .70rem;
        }
        [data-testid="stMetricValue"] {
            color: #ecf6ea;
            font-family: "Rajdhani", sans-serif;
            font-weight: 700;
        }
        .sidebar-shell, .sidebar-note {
            padding: .95rem 1rem;
            margin: 0 0 .9rem 0;
            border-radius: 16px;
            border: 1px solid rgba(158,243,184,.18);
            background: rgba(9,18,12,.78);
        }
        .eyebrow {
            color: #9ef3b8;
            font-size: .72rem;
            letter-spacing: .16em;
            text-transform: uppercase;
        }
        .sidebar-shell h2 { font-size: 1.5rem; }
        .sidebar-shell p, .sidebar-note { margin: .35rem 0 0 0; }
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
            color: #9fb8a4; font-family: "Rajdhani", sans-serif; letter-spacing: .10em; text-transform: uppercase;
        }
        .stTabs [aria-selected="true"] { background: rgba(158,243,184,.14); color: #eaf4e5; }
        .stButton > button, .stDownloadButton > button {
            border-radius: 14px; border: 1px solid rgba(158,243,184,.28); background: rgba(13,28,19,.96);
            color: #eaf4e5; font-family: "Rajdhani", sans-serif; letter-spacing: .08em; text-transform: uppercase;
        }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div,
        [data-testid="stFileUploaderDropzone"], [data-testid="stDataFrame"], [data-testid="stDataEditor"], .stCodeBlock, pre {
            border-radius: 16px !important; border-color: rgba(158,243,184,.18) !important; background: rgba(10,20,14,.76) !important;
        }
        @media (max-width: 900px) { .header-stats { grid-template-columns: 1fr; } .header-copy h1 { font-size: 2rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_percent(value: float, decimals: int = 2) -> str:
    return f"{value * 100:.{decimals}f}%"


def format_eur(value: float, decimals: int = 0, signed: bool = False) -> str:
    prefix = "+" if signed else ""
    return f"{prefix}{value:,.{decimals}f} EUR"


def section(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-intro">
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


def latest_snapshot_date(snapshot: pd.DataFrame) -> str:
    if snapshot.empty:
        return "Unavailable"
    return str(snapshot["rate_date"].max())


def top_exposure_summary(exposure: pd.DataFrame) -> tuple[str, float]:
    non_reporting = exposure.loc[exposure["currency"] != REPORTING_CURRENCY].copy()
    if non_reporting.empty:
        return "EUR only", 0.0
    top_row = non_reporting.sort_values("value_eur", ascending=False).iloc[0]
    return str(top_row["currency"]), float(top_row["value_eur"])


def worst_scenario_summary(scenario_analysis: pd.DataFrame) -> tuple[str, float]:
    if scenario_analysis.empty:
        return "None", 0.0
    worst_row = scenario_analysis.sort_values("scenario_pnl_eur").iloc[0]
    return str(worst_row["currency"]), float(worst_row["scenario_pnl_eur"])


def format_snapshot_table(snapshot: pd.DataFrame) -> pd.DataFrame:
    if snapshot.empty:
        return snapshot
    display = snapshot.loc[:, ["target_currency", "exchange_rate", "rate_date"]].copy()
    display = display.rename(columns={"target_currency": "Currency", "exchange_rate": "Rate", "rate_date": "Date"})
    display["Rate"] = display["Rate"].map(lambda value: f"{value:.4f}")
    return display.sort_values("Currency").reset_index(drop=True)


def format_exposure_table(exposure: pd.DataFrame) -> pd.DataFrame:
    if exposure.empty:
        return exposure
    display = exposure.loc[:, ["currency", "position_count", "value_eur", "portfolio_weight", "fx_pnl_1d_eur"]].copy()
    display = display.rename(
        columns={
            "currency": "Currency",
            "position_count": "Positions",
            "value_eur": "Value (EUR)",
            "portfolio_weight": "Weight",
            "fx_pnl_1d_eur": "1D FX P&L (EUR)",
        }
    )
    display["Value (EUR)"] = display["Value (EUR)"].map(lambda value: f"{value:,.0f}")
    display["Weight"] = display["Weight"].map(lambda value: f"{value * 100:.1f}%")
    display["1D FX P&L (EUR)"] = display["1D FX P&L (EUR)"].map(lambda value: f"{value:,.0f}")
    return display.reset_index(drop=True)


def format_scenario_table(scenario_analysis: pd.DataFrame) -> pd.DataFrame:
    if scenario_analysis.empty:
        return scenario_analysis
    display = scenario_analysis.loc[:, ["currency", "shock_pct", "current_value_eur", "scenario_pnl_eur"]].copy()
    display = display.rename(
        columns={
            "currency": "Currency",
            "shock_pct": "Shock",
            "current_value_eur": "Base Value (EUR)",
            "scenario_pnl_eur": "Scenario P&L (EUR)",
        }
    )
    display["Shock"] = display["Shock"].map(lambda value: f"{value * 100:.2f}%")
    display["Base Value (EUR)"] = display["Base Value (EUR)"].map(lambda value: f"{value:,.0f}")
    display["Scenario P&L (EUR)"] = display["Scenario P&L (EUR)"].map(lambda value: f"{value:,.0f}")
    return display.reset_index(drop=True)


def format_positions_table(positions: pd.DataFrame) -> pd.DataFrame:
    if positions.empty:
        return positions
    display = positions.loc[
        :,
        ["position_id", "position_name", "book", "asset_class", "currency", "value_eur", "fx_pnl_1d_eur"],
    ].copy()
    display = display.rename(
        columns={
            "position_id": "Position ID",
            "position_name": "Position Name",
            "book": "Book",
            "asset_class": "Asset Class",
            "currency": "Currency",
            "value_eur": "Value (EUR)",
            "fx_pnl_1d_eur": "1D FX P&L (EUR)",
        }
    )
    display["Value (EUR)"] = display["Value (EUR)"].map(lambda value: f"{value:,.0f}")
    display["1D FX P&L (EUR)"] = display["1D FX P&L (EUR)"].map(lambda value: f"{value:,.0f}")
    return display.reset_index(drop=True)


def filter_positions(positions: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    filtered = positions.copy()
    books = sorted(book for book in filtered["book"].unique() if book)
    asset_classes = sorted(asset_class for asset_class in filtered["asset_class"].unique() if asset_class)

    filter_columns = st.columns(2)
    selected_books = filter_columns[0].multiselect("Book", options=books, default=books, key=f"{key_prefix}_books")
    selected_asset_classes = filter_columns[1].multiselect(
        "Asset class",
        options=asset_classes,
        default=asset_classes,
        key=f"{key_prefix}_asset_classes",
    )

    if books:
        filtered = filtered[filtered["book"].isin(selected_books)] if selected_books else filtered.iloc[0:0]
    if asset_classes:
        filtered = filtered[filtered["asset_class"].isin(selected_asset_classes)] if selected_asset_classes else filtered.iloc[0:0]

    return filtered.reset_index(drop=True)


def render_header(market_result: dict, portfolio_analysis: dict, focus_currency: str, portfolio_rows: int) -> None:
    snapshot = market_result["latest_snapshot"]
    top_currency, top_value = top_exposure_summary(portfolio_analysis["currency_exposure"])
    snapshot_count = int(snapshot["target_currency"].nunique()) if not snapshot.empty else 0
    st.markdown(
        f"""
        <div class="page-header">
            <div class="status-line">
                <span class="status-chip">ECB reference rates</span>
                <span class="status-chip">Focus EUR/{focus_currency}</span>
                <span class="status-chip">Rates as of {latest_snapshot_date(snapshot)}</span>
            </div>
            <div class="header-row">
                <div class="header-copy">
                    <h1>EUR FX Risk Dashboard</h1>
                    <p>
                        Track ECB reference rates, portfolio exposure, and stress outcomes without digging
                        through separate screens or infrastructure details.
                    </p>
                </div>
                <div class="header-stats">
                    <div class="header-stat"><span>Portfolio rows</span><strong>{portfolio_rows:,}</strong></div>
                    <div class="header-stat"><span>Snapshot currencies</span><strong>{snapshot_count}</strong></div>
                    <div class="header-stat"><span>Largest FX exposure</span><strong>{top_currency}</strong></div>
                    <div class="header-stat"><span>Exposure size</span><strong>{format_eur(top_value)}</strong></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_tab(market_result: dict, portfolio_analysis: dict, focus_currency: str) -> None:
    section(
        "Overview",
        "Start here. This screen answers what changed, where the risk sits, and which EUR cross deserves attention first.",
    )

    portfolio_summary = portfolio_analysis["summary"]
    market_summary = market_result["summary"]
    exposure = portfolio_analysis["currency_exposure"]
    non_reporting_exposure = exposure.loc[exposure["currency"] != REPORTING_CURRENCY].copy()
    top_currency, top_value = top_exposure_summary(exposure)

    metrics = st.columns(5)
    metrics[0].metric("Portfolio Value", format_eur(portfolio_summary["portfolio_value_eur"]))
    metrics[1].metric("1D FX P&L", format_eur(portfolio_summary["fx_pnl_1d_eur"], signed=True))
    metrics[2].metric(
        f"{int(portfolio_summary['confidence_level'] * 100)}% 1D VaR",
        format_eur(portfolio_summary["historical_var_1d_eur"]),
    )
    metrics[3].metric("Largest FX Exposure", top_currency, delta=format_eur(top_value))
    metrics[4].metric(
        f"EUR/{focus_currency}",
        f"{market_summary['latest_rate']:.4f}",
        delta=format_percent(market_summary["period_return"]),
    )

    st.altair_chart(
        line_chart(
            portfolio_analysis["portfolio_value_history"],
            "rate_date:T",
            "portfolio_value_eur:Q",
            GREEN,
            "Portfolio value path",
        ),
        use_container_width=True,
    )

    lower_columns = st.columns((1, 1))
    with lower_columns[0]:
        if non_reporting_exposure.empty:
            st.info("No non-EUR exposure is present in the current portfolio.")
        else:
            st.altair_chart(
                bar_chart(
                    non_reporting_exposure.head(8),
                    "currency:N",
                    "value_eur:Q",
                    GREEN_DIM,
                    "Largest non-EUR exposures",
                ),
                use_container_width=True,
            )
    with lower_columns[1]:
        st.altair_chart(
            line_chart(
                market_result["history"],
                "rate_date:T",
                "exchange_rate:Q",
                AMBER,
                f"EUR/{focus_currency} rate history",
            ),
            use_container_width=True,
        )


def render_portfolio_risk_tab(
    cleaned_portfolio: pd.DataFrame,
    lookback_days: int,
    confidence_level: float,
    rolling_window: int,
    frequency: str,
) -> None:
    section(
        "Portfolio Risk",
        "Drill into a book or asset class. The table stays ranked by EUR value so concentration stays obvious.",
    )

    with st.expander("Filters", expanded=True):
        filtered_positions = filter_positions(cleaned_portfolio, "risk")

    if filtered_positions.empty:
        st.warning("No positions remain after the selected filters.")
        return

    analysis = get_portfolio_analysis_result(
        portfolio_csv=filtered_positions.to_csv(index=False),
        lookback_days=lookback_days,
        confidence_level=confidence_level,
        rolling_window=rolling_window,
        frequency=frequency,
        scenario_shocks=tuple(),
    )

    summary = analysis["summary"]
    exposure = analysis["currency_exposure"]
    non_reporting_exposure = exposure.loc[exposure["currency"] != REPORTING_CURRENCY].copy()

    metrics = st.columns(5)
    metrics[0].metric("Portfolio Value", format_eur(summary["portfolio_value_eur"]))
    metrics[1].metric("Non-EUR Share", format_percent(summary["non_eur_share"], decimals=1))
    metrics[2].metric("Annualized Volatility", format_percent(summary["annualized_portfolio_volatility"]))
    metrics[3].metric("Positions", f"{summary['position_count']}")
    metrics[4].metric("Currencies", f"{summary['currency_count']}")

    st.dataframe(format_exposure_table(exposure), use_container_width=True, hide_index=True)

    visuals = st.columns((1.05, 0.95))
    with visuals[0]:
        if non_reporting_exposure.empty:
            st.info("No non-EUR exposure is present in the selected slice.")
        else:
            st.altair_chart(
                bar_chart(
                    non_reporting_exposure.head(8),
                    "currency:N",
                    "value_eur:Q",
                    GREEN_DIM,
                    "Exposure by currency",
                ),
                use_container_width=True,
            )
    with visuals[1]:
        if analysis["correlation_matrix"].empty:
            st.info("Correlation requires at least two non-EUR currencies with overlapping history.")
        else:
            st.altair_chart(heatmap_chart(analysis["correlation_matrix"]), use_container_width=True)

    st.altair_chart(
        line_chart(
            analysis["portfolio_value_history"],
            "rate_date:T",
            "portfolio_value_eur:Q",
            GREEN,
            "Filtered portfolio value path",
        ),
        use_container_width=True,
    )

    with st.expander("Position detail"):
        st.dataframe(format_positions_table(analysis["positions"]), use_container_width=True, hide_index=True)


def render_stress_test_tab(
    cleaned_portfolio: pd.DataFrame,
    lookback_days: int,
    confidence_level: float,
    rolling_window: int,
    frequency: str,
) -> None:
    section(
        "Stress Test",
        "Set directional shocks and inspect the resulting P&L by currency for the selected portfolio slice.",
    )

    with st.expander("Scope", expanded=True):
        filtered_positions = filter_positions(cleaned_portfolio, "stress")

    if filtered_positions.empty:
        st.warning("No positions remain after the selected filters.")
        return

    scenario_base = pd.DataFrame(
        {
            "currency": [
                currency
                for currency in sorted(filtered_positions["currency"].unique())
                if currency != REPORTING_CURRENCY
            ],
            "shock_pct": 0.0,
        }
    )

    if scenario_base.empty:
        st.info("The selected scope contains only EUR positions, so there is no FX stress to run.")
        return

    editor_column, output_column = st.columns((0.8, 1.2))
    with editor_column:
        st.caption("Positive shock means EUR strengthens against the selected currency.")
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

    scenario_analysis = analysis["scenario_analysis"]
    worst_currency, worst_pnl = worst_scenario_summary(scenario_analysis)

    with output_column:
        metrics = st.columns(3)
        metrics[0].metric("Scenario Total", format_eur(analysis["summary"]["scenario_total_pnl_eur"], signed=True))
        metrics[1].metric("Worst Currency", worst_currency, delta=format_eur(worst_pnl, signed=True))
        metrics[2].metric("Shocks Applied", str(len(scenario_shocks)))

        if not scenario_shocks:
            st.info("All shocks are set to 0.00%. Update one or more rows to run a non-flat scenario.")

        st.altair_chart(
            bar_chart(
                scenario_analysis,
                "currency:N",
                "scenario_pnl_eur:Q",
                RED,
                "Scenario P&L by currency",
                directional=True,
            ),
            use_container_width=True,
        )

    st.dataframe(format_scenario_table(scenario_analysis), use_container_width=True, hide_index=True)


def render_data_tab(
    market_result: dict,
    currency_catalog: pd.DataFrame,
    lookback_days: int,
    frequency: str,
) -> None:
    section(
        "Data & API",
        "Reference data, source freshness, and the integration contract behind the dashboard.",
    )

    snapshot = market_result["latest_snapshot"]
    metrics = st.columns(4)
    metrics[0].metric("Rates As Of", latest_snapshot_date(snapshot))
    metrics[1].metric("Snapshot Currencies", f"{snapshot['target_currency'].nunique() if not snapshot.empty else 0}")
    metrics[2].metric("Supported Currencies", f"{len(currency_catalog)}")
    metrics[3].metric("Lookback Window", f"{lookback_days} days")

    columns = st.columns((1.1, 0.9))
    with columns[0]:
        st.dataframe(format_snapshot_table(snapshot), use_container_width=True, hide_index=True)
    with columns[1]:
        st.markdown(
            f"""
            <div class="table-shell">
                <p><strong>Source</strong>: ECB reference rates via Euro Rates API.</p>
                <p><strong>Reporting currency</strong>: {REPORTING_CURRENCY}</p>
                <p><strong>History frequency</strong>: {frequency}</p>
                <p><strong>Purpose</strong>: EUR rate monitoring, exposure analysis, and scenario testing.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("API routes"):
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

    with st.expander("Portfolio CSV contract"):
        st.code(
            """\
position_id,position_name,asset_class,book,currency,market_value_local
EQ-USD-01,US Equity Sleeve,Equity,Global Macro,USD,250000
BOND-GBP-01,UK Gilts,Bonds,Macro Rates,GBP,180000
""",
            language="csv",
        )

    with st.expander("Run locally"):
        st.code(
            """\
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r requirements.txt
.\\.venv\\Scripts\\python -m streamlit run dashboard\\app.py
.\\.venv\\Scripts\\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
""",
            language="powershell",
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
                <div class="eyebrow">Controls</div>
                <h2>Core Inputs</h2>
                <p>Pick the focus pair and load a portfolio. Daily settings below are already tuned for a typical review.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        focus_currency = st.selectbox(
            "Focus currency",
            options=currency_options,
            index=currency_options.index("USD") if "USD" in currency_options else 0,
        )
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
            <div class="sidebar-note">
                Defaults are set for a daily EUR portfolio workflow. Open advanced settings only if you need to change the horizon or model parameters.
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Advanced settings"):
            market_currencies = st.multiselect(
                "Market snapshot currencies",
                options=currency_options,
                default=default_market_currencies or currency_options[:6],
            )
            frequency = st.selectbox("Frequency", options=["D", "M", "Q", "A"], index=0)
            lookback_days = st.slider("Lookback window", min_value=30, max_value=365, value=180, step=30)
            confidence_level = st.slider("VaR confidence level", min_value=0.80, max_value=0.99, value=0.95, step=0.01)
            rolling_window = st.slider("Rolling volatility window", min_value=5, max_value=60, value=20, step=1)
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
        portfolio_frame, _portfolio_message = load_portfolio_input(uploaded_portfolio)
        cleaned_portfolio = clean_portfolio_positions(portfolio_frame)
        overview_analysis = get_portfolio_analysis_result(
            portfolio_csv=cleaned_portfolio.to_csv(index=False),
            lookback_days=lookback_days,
            confidence_level=confidence_level,
            rolling_window=rolling_window,
            frequency=frequency,
            scenario_shocks=tuple(),
        )
    except Exception as exc:
        st.error(f"Unable to load dashboard data: {exc}")
        st.stop()

    render_header(
        market_result=market_result,
        portfolio_analysis=overview_analysis,
        focus_currency=focus_currency,
        portfolio_rows=len(cleaned_portfolio),
    )

    overview_tab, risk_tab, stress_tab, data_tab = st.tabs(["Overview", "Portfolio Risk", "Stress Test", "Data & API"])
    with overview_tab:
        render_overview_tab(
            market_result=market_result,
            portfolio_analysis=overview_analysis,
            focus_currency=focus_currency,
        )
    with risk_tab:
        render_portfolio_risk_tab(
            cleaned_portfolio=cleaned_portfolio,
            lookback_days=lookback_days,
            confidence_level=confidence_level,
            rolling_window=rolling_window,
            frequency=frequency,
        )
    with stress_tab:
        render_stress_test_tab(
            cleaned_portfolio=cleaned_portfolio,
            lookback_days=lookback_days,
            confidence_level=confidence_level,
            rolling_window=rolling_window,
            frequency=frequency,
        )
    with data_tab:
        render_data_tab(
            market_result=market_result,
            currency_catalog=currency_catalog,
            lookback_days=lookback_days,
            frequency=frequency,
        )


if __name__ == "__main__":
    main()
