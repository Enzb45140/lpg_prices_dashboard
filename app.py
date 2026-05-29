"""
LPG Market Daily Dashboard
Reads from: ms_cad_lpgdbw_poc_catalog.alvaro_test.lpg_daily_prices
Auth:        Databricks OAuth M2M (Service Principal)
Deploy:      streamlit run app.py  OR  Streamlit Community Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from databricks import sql
import datetime

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LPG Market Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# TICKER REGISTRY
# ─────────────────────────────────────────────────────────────
TICKERS = {
    # US Physical
    'PMAAY00': {'label': 'Propane Mt Belvieu M1',        'group': '🇺🇸 US Physical',      'color': '#3b82f6'},
    'AAWUD00': {'label': 'Propane Mt Belvieu M2',        'group': '🇺🇸 US Physical',      'color': '#60a5fa'},
    'PMAAI00': {'label': 'Butane Mt Belvieu M1',         'group': '🇺🇸 US Physical',      'color': '#93c5fd'},
    # US Swaps
    'AAHYX00': {'label': 'Propane USGC Swap M1',         'group': '🇺🇸 US Swaps',         'color': '#1d4ed8'},
    'AAHYY00': {'label': 'Propane USGC Swap M2',         'group': '🇺🇸 US Swaps',         'color': '#2563eb'},
    'AAHYZ00': {'label': 'Propane USGC Swap M3',         'group': '🇺🇸 US Swaps',         'color': '#3b82f6'},
    # US Exports
    'AAXIM00': {'label': 'Propane FOB USGC $/mt',        'group': '🇺🇸 US Exports',       'color': '#0ea5e9'},
    'AAXIO00': {'label': 'Propane FOB USGC vs Belvieu',  'group': '🇺🇸 US Exports',       'color': '#38bdf8'},
    # Europe Physical
    'PMABA00': {'label': 'Propane CIF NWE Large',        'group': '🇪🇺 Europe Physical',  'color': '#16a34a'},
    'PMAAS00': {'label': 'Propane FOB ARA',              'group': '🇪🇺 Europe Physical',  'color': '#22c55e'},
    'PMABH00': {'label': 'Propane FCA ARA',              'group': '🇪🇺 Europe Physical',  'color': '#4ade80'},
    # Europe Swaps
    'AAHIK00': {'label': 'Propane CIF NWE Swap M1',      'group': '🇪🇺 Europe Swaps',     'color': '#059669'},
    'AAHIM00': {'label': 'Propane CIF NWE Swap M2',      'group': '🇪🇺 Europe Swaps',     'color': '#10b981'},
    'AAHIO00': {'label': 'Propane CIF NWE Swap M3',      'group': '🇪🇺 Europe Swaps',     'color': '#34d399'},
    # Europe Spreads
    'PNM0102': {'label': 'Propane NWE M1/M2 Spread',     'group': '🇪🇺 Europe Spreads',   'color': '#6ee7b7'},
    'PNM0203': {'label': 'Propane NWE M2/M3 Spread',     'group': '🇪🇺 Europe Spreads',   'color': '#a7f3d0'},
    # EU LPG/Naphtha
    'AAYJA00': {'label': 'Propane vs Naphtha NWE M1',    'group': '🇪🇺 EU Switch Signal', 'color': '#d97706'},
    'AAYJB00': {'label': 'Propane vs Naphtha NWE M2',    'group': '🇪🇺 EU Switch Signal', 'color': '#f59e0b'},
    # Asia Physical
    'AAVAK00': {'label': 'Propane CFR N.Asia 30-45d',    'group': '🌏 Asia Physical',     'color': '#ef4444'},
    'AAVAL00': {'label': 'Propane CFR N.Asia 45-60d',    'group': '🌏 Asia Physical',     'color': '#f87171'},
    'AAVAM00': {'label': 'Propane CFR N.Asia 60-75d',    'group': '🌏 Asia Physical',     'color': '#fca5a5'},
    # Asia Cash Diffs
    'PMAAX00': {'label': 'Propane CFR N.Asia vs SCP M1', 'group': '🌏 Asia Cash Diff',    'color': '#dc2626'},
    'PMAAH00': {'label': 'Butane CFR N.Asia vs SCP M1',  'group': '🌏 Asia Cash Diff',    'color': '#b91c1c'},
    'AABAI00': {'label': 'Propane CFR S.China vs SCP',   'group': '🌏 Asia Cash Diff',    'color': '#991b1b'},
    'AABAK00': {'label': 'Propane Refrig CFR S.China',   'group': '🌏 Asia Physical',     'color': '#fca5a5'},
    'AABAT00': {'label': 'Butane CFR S.China vs SCP',    'group': '🌏 Asia Cash Diff',    'color': '#7f1d1d'},
    'AABAU00': {'label': 'Butane Refrig CFR S.China',    'group': '🌏 Asia Physical',     'color': '#fee2e2'},
    # SE Asia
    'AAWUV00': {'label': 'LPG CFR Vietnam 7-15d',        'group': '🌏 SE Asia',           'color': '#f97316'},
    'AAWUW00': {'label': 'LPG CFR Vietnam vs SCP',       'group': '🌏 SE Asia',           'color': '#fb923c'},
    'AAWUX00': {'label': 'LPG CFR Philippines 7-15d',    'group': '🌏 SE Asia',           'color': '#fdba74'},
    'AAWUZ00': {'label': 'LPG FOB East China 7-15d',     'group': '🌏 SE Asia',           'color': '#fed7aa'},
    # Middle East
    'PMUDM00': {'label': 'Propane FOB Arab Gulf',        'group': '🌍 Middle East',       'color': '#7c3aed'},
    'PMUDR00': {'label': 'Butane FOB Arab Gulf',         'group': '🌍 Middle East',       'color': '#8b5cf6'},
    'PMABF00': {'label': 'Propane FOB AG vs Saudi CP',   'group': '🌍 ME Cash Diff',      'color': '#a78bfa'},
    'PMABG00': {'label': 'Butane FOB AG vs Saudi CP',    'group': '🌍 ME Cash Diff',      'color': '#c4b5fd'},
    # Saudi CP
    'AAHHG00': {'label': 'Saudi CP Propane Swap M1',     'group': '💡 Saudi CP',          'color': '#f59e0b'},
    'AAHHH00': {'label': 'Saudi CP Propane Swap M2',     'group': '💡 Saudi CP',          'color': '#fbbf24'},
    'AAHHI00': {'label': 'Saudi CP Propane Swap M3',     'group': '💡 Saudi CP',          'color': '#fcd34d'},
    # Freight
    'AAPNI00': {'label': 'VLGC PG → Japan 44kt',        'group': '🚢 Freight',           'color': '#64748b'},
    'AAPNH00': {'label': 'VLGC PG → E.China 44kt',      'group': '🚢 Freight',           'color': '#94a3b8'},
    'AAPNG00': {'label': 'VLGC PG → S.China 44kt',      'group': '🚢 Freight',           'color': '#cbd5e1'},
    'AAXIS00': {'label': 'VLGC Houston → Japan',         'group': '🚢 Freight',           'color': '#475569'},
    'AAXIQ00': {'label': 'VLGC Houston → NWE',           'group': '🚢 Freight',           'color': '#334155'},
    # Naphtha
    'PAAAL00': {'label': 'Naphtha CIF NWE',              'group': '🛢️ Naphtha',           'color': '#78716c'},
    'PAAAD00': {'label': 'Naphtha CFR Japan',            'group': '🛢️ Naphtha',           'color': '#a8a29e'},
    # Time Spreads
    'LPM0102': {'label': 'Propane USGC M1/M2 Spread',   'group': '📈 Time Spreads',      'color': '#ec4899'},
    'LPM0203': {'label': 'Propane USGC M2/M3 Spread',   'group': '📈 Time Spreads',      'color': '#f9a8d4'},
    # Crude
    'AAWS001': {'label': 'WTI M1 (NYMEX Settle)',        'group': '🛢️ Crude',             'color': '#292524'},
}

CHART_TEMPLATE = 'plotly_dark'

# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────
import requests

@st.cache_data(ttl=3600, show_spinner="Loading prices from Databricks...")
def load_data(lookback_days: int = 365 * 3) -> pd.DataFrame:
    since = (datetime.date.today() - datetime.timedelta(days=lookback_days)).isoformat()

    # Step 1: get Azure AD token for the SP
    tenant_id     = st.secrets["DATABRICKS_TENANT_ID"]
    client_id     = st.secrets["DATABRICKS_CLIENT_ID"]
    client_secret = st.secrets["DATABRICKS_CLIENT_SECRET"]

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    token_resp = requests.post(token_url, data={
        "grant_type":    "client_credentials",
        "client_id":     client_id,
        "client_secret": client_secret,
        "resource":      "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d",  # Databricks resource ID (fixed)
    })
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    # Step 2: connect using the token
    with sql.connect(
        server_hostname = st.secrets["DATABRICKS_HOST"],
        http_path       = st.secrets["DATABRICKS_HTTP_PATH"],
        access_token    = access_token,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT publication_date, price_code, description, price
                FROM ms_cad_lpgdbw_poc_catalog.alvaro_test.lpg_daily_prices
                WHERE publication_date >= '{since}'
                ORDER BY publication_date, price_code
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

    df = pd.DataFrame(rows, columns=cols)
    df['publication_date'] = pd.to_datetime(df['publication_date'])
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    return df

def pivot(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(
        index='publication_date',
        columns='price_code',
        values='price',
        aggfunc='last'
    ).sort_index()

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def chg(wide: pd.DataFrame, col: str, periods: int):
    if col not in wide.columns:
        return np.nan
    s = wide[col].dropna()
    if len(s) <= periods:
        return np.nan
    return round(s.iloc[-1] - s.iloc[-1 - periods], 2)

def pct(wide: pd.DataFrame, col: str, periods: int):
    if col not in wide.columns:
        return np.nan
    s = wide[col].dropna()
    if len(s) <= periods:
        return np.nan
    return round((s.iloc[-1] / s.iloc[-1 - periods] - 1) * 100, 2)

def last(wide: pd.DataFrame, col: str):
    if col not in wide.columns:
        return np.nan
    s = wide[col].dropna()
    return round(s.iloc[-1], 2) if not s.empty else np.nan

def fmt_chg(val):
    if pd.isna(val):
        return "—"
    arrow = "▲" if val > 0 else ("▼" if val < 0 else "—")
    color = "green" if val > 0 else ("red" if val < 0 else "gray")
    return f":{color}[{arrow} {abs(val):.2f}]"

def line_chart(wide, tickers, title, height=380, zero_line=False):
    fig = go.Figure()
    for t in tickers:
        if t not in wide.columns:
            continue
        m = TICKERS.get(t, {})
        fig.add_trace(go.Scatter(
            x=wide.index, y=wide[t],
            name=m.get('label', t),
            line=dict(color=m.get('color', '#94a3b8'), width=1.8),
            hovertemplate='%{x|%d %b %Y}  <b>%{y:.2f}</b><extra>' + m.get('label', t) + '</extra>',
        ))
    if zero_line:
        fig.add_hline(y=0, line_dash='dot', line_color='#475569', line_width=1)
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=title, height=height,
        legend=dict(orientation='h', y=-0.25, font_size=10),
        hovermode='x unified',
        margin=dict(t=40, b=10, l=10, r=10),
    )
    return fig

# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    # ── Header ───────────────────────────────────────────────
    col_title, col_refresh = st.columns([6, 1])
    with col_title:
        st.markdown("## ⚡ LPG Market Dashboard")
    with col_refresh:
        if st.button("↻ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # ── Load ─────────────────────────────────────────────────
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"Connection error: {e}")
        st.info("Check your .streamlit/secrets.toml credentials.")
        return

    wide = pivot(df_raw)
    latest_date = wide.index.max()
    st.caption(f"Last update: **{latest_date.strftime('%A %d %b %Y')}** — {len(wide.columns)} series loaded")

    # ── Tabs ─────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📈 Forward Curves",
        "🔀 Spreads & Arbs",
        "🚢 Freight",
        "📋 Full Watchlist",
    ])

    # ════════════════════════════════════════════════════════
    # TAB 1 — OVERVIEW
    # ════════════════════════════════════════════════════════
    with tab1:
        # KPI cards — top 6
        kpi_tickers = ['PMAAY00', 'PMABA00', 'AAVAK00', 'PMUDM00', 'AAHHG00', 'AAPNI00']
        cols = st.columns(len(kpi_tickers))
        for col, t in zip(cols, kpi_tickers):
            m   = TICKERS.get(t, {})
            val = last(wide, t)
            d1  = chg(wide, t, 1)
            with col:
                st.metric(
                    label=m.get('label', t),
                    value=f"{val:.2f}" if not np.isnan(val) else "N/A",
                    delta=f"{d1:+.2f}" if not np.isnan(d1) else None,
                )
                st.caption(t)

        st.divider()

        # Lookback selector
        lb = st.select_slider(
            "Lookback window",
            options=[30, 60, 90, 180, 365, 730],
            value=180,
            format_func=lambda x: f"{x}d" if x < 365 else f"{x//365}y",
        )
        wide_lb = wide.tail(lb)

        # 2x2 outright grid
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                line_chart(wide_lb, ['PMAAY00','AAHYX00','AAHYY00','AAHYZ00'], '🇺🇸 US Propane'),
                use_container_width=True,
            )
        with c2:
            st.plotly_chart(
                line_chart(wide_lb, ['PMABA00','PMAAS00','AAHIK00','AAHIM00','AAHIO00'], '🇪🇺 Europe Propane'),
                use_container_width=True,
            )
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(
                line_chart(wide_lb, ['AAVAK00','AAVAL00','AAVAM00'], '🌏 Asia CFR N.Asia'),
                use_container_width=True,
            )
        with c4:
            st.plotly_chart(
                line_chart(wide_lb, ['PMUDM00','PMUDR00','AAHHG00','AAHHH00'], '🌍 ME & Saudi CP'),
                use_container_width=True,
            )

    # ════════════════════════════════════════════════════════
    # TAB 2 — FORWARD CURVES
    # ════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Swap curve snapshot — latest close")

        # Bar chart M1/M2/M3 for 3 markets
        markets = {
            'USGC Propane':  ['AAHYX00','AAHYY00','AAHYZ00'],
            'NWE Propane':   ['AAHIK00','AAHIM00','AAHIO00'],
            'Saudi CP':      ['AAHHG00','AAHHH00','AAHHI00'],
        }
        tenors  = ['M1','M2','M3']
        colors  = ['#3b82f6','#60a5fa','#93c5fd']

        fig_bar = go.Figure()
        for market, tks in markets.items():
            vals = [last(wide, t) for t in tks]
            for i, (tenor, val, color) in enumerate(zip(tenors, vals, colors)):
                fig_bar.add_trace(go.Bar(
                    name=f"{market} {tenor}",
                    x=[f"{market} {tenor}"],
                    y=[val],
                    marker_color=color,
                    text=[f"{val:.1f}" if not np.isnan(val) else "N/A"],
                    textposition='outside',
                    showlegend=(market == 'USGC Propane'),
                ))
        fig_bar.update_layout(
            template=CHART_TEMPLATE,
            barmode='group', height=380,
            yaxis_title='$/mt',
            margin=dict(t=20, b=10),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.subheader("Curve structure over time")

        sel_market = st.radio(
            "Market", ['USGC Propane', 'NWE Propane', 'Saudi CP'],
            horizontal=True,
        )
        market_tickers = {
            'USGC Propane': ['AAHYX00','AAHYY00','AAHYZ00'],
            'NWE Propane':  ['AAHIK00','AAHIM00','AAHIO00'],
            'Saudi CP':     ['AAHHG00','AAHHH00','AAHHI00'],
        }
        lb2 = st.slider("Days", 30, 365, 180, key='lb2')
        st.plotly_chart(
            line_chart(wide.tail(lb2), market_tickers[sel_market], sel_market, height=350),
            use_container_width=True,
        )

        # Time spreads
        st.divider()
        st.subheader("Time spreads (M1–M2) — structure signal")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                line_chart(wide.tail(180), ['LPM0102','LPM0203'], '🇺🇸 USGC M1/M2 & M2/M3', zero_line=True),
                use_container_width=True,
            )
        with c2:
            st.plotly_chart(
                line_chart(wide.tail(180), ['PNM0102','PNM0203'], '🇪🇺 NWE M1/M2 & M2/M3', zero_line=True),
                use_container_width=True,
            )

    # ════════════════════════════════════════════════════════
    # TAB 3 — SPREADS & ARBS
    # ════════════════════════════════════════════════════════
    with tab3:
        lb3 = st.slider("Days", 30, 730, 180, key='lb3')
        wide_s = wide.tail(lb3)

        st.subheader("Asia cash diffs vs Saudi CP")
        st.plotly_chart(
            line_chart(wide_s, ['PMAAX00','PMAAH00','AABAI00','AABAT00'],
                       'Asia Cash Diffs', zero_line=True),
            use_container_width=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("SE Asia (Vietnam / Philippines)")
            st.plotly_chart(
                line_chart(wide_s, ['AAWUV00','AAWUX00','AAWUZ00'],
                           'SE Asia Outrights', height=320),
                use_container_width=True,
            )
            st.plotly_chart(
                line_chart(wide_s, ['AAWUW00'],
                           'Vietnam vs Saudi CP diff', height=280, zero_line=True),
                use_container_width=True,
            )
        with c2:
            st.subheader("EU LPG vs Naphtha — switch signal")
            st.plotly_chart(
                line_chart(wide_s, ['AAYJA00','AAYJB00'],
                           'Propane vs Naphtha NWE M1/M2', height=320, zero_line=True),
                use_container_width=True,
            )
            st.subheader("US export premium")
            st.plotly_chart(
                line_chart(wide_s, ['AAXIO00'],
                           'FOB USGC vs Mt Belvieu $/mt', height=280, zero_line=True),
                use_container_width=True,
            )

        st.divider()
        st.subheader("ME cash diffs at origin")
        st.plotly_chart(
            line_chart(wide_s, ['PMABF00','PMABG00'],
                       'FOB Arab Gulf vs Saudi CP — Propane & Butane',
                       height=300, zero_line=True),
            use_container_width=True,
        )

        st.subheader("Naphtha benchmarks — feedstock context")
        st.plotly_chart(
            line_chart(wide_s, ['PAAAL00','PAAAD00'],
                       'Naphtha CIF NWE & CFR Japan', height=300),
            use_container_width=True,
        )

    # ════════════════════════════════════════════════════════
    # TAB 4 — FREIGHT
    # ════════════════════════════════════════════════════════
    with tab4:
        lb4 = st.slider("Days", 30, 730, 180, key='lb4')

        # KPI row
        freight_kpis = ['AAPNI00','AAPNH00','AAPNG00','AAXIS00','AAXIQ00']
        cols = st.columns(len(freight_kpis))
        for col, t in zip(cols, freight_kpis):
            m   = TICKERS.get(t, {})
            val = last(wide, t)
            d1  = chg(wide, t, 1)
            with col:
                st.metric(
                    label=m['label'],
                    value=f"{val:.1f}" if not np.isnan(val) else "N/A",
                    delta=f"{d1:+.1f}" if not np.isnan(d1) else None,
                )

        st.plotly_chart(
            line_chart(
                wide.tail(lb4),
                ['AAPNI00','AAPNH00','AAPNG00','AAXIS00','AAXIQ00'],
                'VLGC Freight Rates ($/mt)',
                height=420,
            ),
            use_container_width=True,
        )

        # Arb cost vs diff
        st.divider()
        st.subheader("Arb check — Asia cash diff vs freight cost")
        st.caption("If cash diff > freight, the arb is theoretically open.")

        wide_arb = wide.tail(lb4)[['PMAAX00','AAPNI00']].dropna()
        if not wide_arb.empty:
            fig_arb = go.Figure()
            fig_arb.add_trace(go.Scatter(
                x=wide_arb.index, y=wide_arb['PMAAX00'],
                name='N.Asia vs SCP M1 (cash diff)',
                line=dict(color='#ef4444', width=2),
            ))
            fig_arb.add_trace(go.Scatter(
                x=wide_arb.index, y=wide_arb['AAPNI00'],
                name='PG→Japan freight',
                line=dict(color='#64748b', width=1.5, dash='dot'),
            ))
            fig_arb.update_layout(
                template=CHART_TEMPLATE,
                height=350,
                hovermode='x unified',
                legend=dict(orientation='h', y=-0.25),
                margin=dict(t=20, b=10),
            )
            st.plotly_chart(fig_arb, use_container_width=True)

    # ════════════════════════════════════════════════════════
    # TAB 5 — FULL WATCHLIST
    # ════════════════════════════════════════════════════════
    with tab5:
        st.subheader("Full price watchlist — all tickers")

        rows = []
        for ticker, meta in TICKERS.items():
            if ticker not in wide.columns:
                continue
            val = last(wide, ticker)
            if np.isnan(val):
                continue
            rows.append({
                'Ticker':     ticker,
                'Description': meta['label'],
                'Group':      meta['group'],
                'Latest':     val,
                '1D':         chg(wide, ticker, 1),
                '1W':         chg(wide, ticker, 5),
                '1M':         chg(wide, ticker, 21),
                '1D %':       pct(wide, ticker, 1),
                '52W High':   round(wide[ticker].rolling(252).max().iloc[-1], 2),
                '52W Low':    round(wide[ticker].rolling(252).min().iloc[-1], 2),
            })

        summary = pd.DataFrame(rows).sort_values(['Group','Ticker'])

        # Group filter
        groups = ['All'] + sorted(summary['Group'].unique().tolist())
        sel_group = st.selectbox("Filter by group", groups)
        if sel_group != 'All':
            summary = summary[summary['Group'] == sel_group]

        def color_val(val):
            if isinstance(val, float) and not np.isnan(val):
                if val > 0:   return 'color: #4ade80'
                if val < 0:   return 'color: #f87171'
            return ''

        styled = (
            summary.style
            .applymap(color_val, subset=['1D','1W','1M','1D %'])
            .format({
                'Latest': '{:.2f}', '1D': '{:+.2f}', '1W': '{:+.2f}',
                '1M': '{:+.2f}', '1D %': '{:+.2f}%',
                '52W High': '{:.2f}', '52W Low': '{:.2f}',
            }, na_rep='—')
            .hide(axis='index')
        )
        st.dataframe(styled, use_container_width=True, height=600)

        # Download button
        csv = summary.to_csv(index=False).encode()
        st.download_button(
            "⬇ Download CSV",
            data=csv,
            file_name=f"lpg_prices_{latest_date.date()}.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
