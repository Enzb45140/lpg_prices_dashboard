# Databricks notebook source
# ============================================================
#  LPG MARKET DAILY DASHBOARD
#  Run every morning to track the global LPG market
#  Author: generated for Platts / ms_atlas data
# ============================================================

# COMMAND ----------
# %pip install plotly kaleido --quiet   # uncomment if not installed

# COMMAND ----------
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from IPython.display import display, HTML
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────
# 1.  TICKER REGISTRY  (label · group · color)
# ─────────────────────────────────────────────────────────────
TICKER_CONFIG = {
    # ── US PHYSICAL ──────────────────────────────────────────
    'PMAAY00': {'label': 'Propane Mt Belvieu M1',        'group': '🇺🇸 US Physical',     'color': '#3b82f6'},
    'PMABQ00': {'label': 'Propane ET Mt Belvieu M1',     'group': '🇺🇸 US Physical',     'color': '#60a5fa'},
    'PMAAT00': {'label': 'Propane Conway Pipeline',      'group': '🇺🇸 US Physical',     'color': '#93c5fd'},
    # ── US SWAPS ─────────────────────────────────────────────
    'AAHYX00': {'label': 'Propane USGC Swap M1',         'group': '🇺🇸 US Swaps',        'color': '#1d4ed8'},
    'AAHYY00': {'label': 'Propane USGC Swap M2',         'group': '🇺🇸 US Swaps',        'color': '#2563eb'},
    'AAHYZ00': {'label': 'Propane USGC Swap M3',         'group': '🇺🇸 US Swaps',        'color': '#3b82f6'},
    # ── US EXPORTS ───────────────────────────────────────────
    'AAXIM00': {'label': 'Propane FOB USGC $/mt',        'group': '🇺🇸 US Exports',      'color': '#0ea5e9'},
    'AAXIO00': {'label': 'Propane FOB USGC vs Belvieu',  'group': '🇺🇸 US Exports',      'color': '#38bdf8'},

    # ── EUROPE PHYSICAL ──────────────────────────────────────
    'PMABA00': {'label': 'Propane CIF NWE Large',        'group': '🇪🇺 Europe Physical', 'color': '#16a34a'},
    'PMAAS00': {'label': 'Propane FOB ARA',              'group': '🇪🇺 Europe Physical', 'color': '#22c55e'},
    'PMABH00': {'label': 'Propane FCA ARA',              'group': '🇪🇺 Europe Physical', 'color': '#4ade80'},
    'PMABB00': {'label': 'Propane FOB NWE Seagoing',     'group': '🇪🇺 Europe Detail',   'color': '#15803d'},
    'PMABE00': {'label': 'Propane CIF West Med 7kt+',    'group': '🇪🇺 Europe Detail',   'color': '#166534'},
    'PMABC00': {'label': 'Propane FOB West Med Ex-Ref',  'group': '🇪🇺 Europe Detail',   'color': '#14532d'},
    # ── EUROPE SWAPS ─────────────────────────────────────────
    'AAHIK00': {'label': 'Propane CIF NWE Swap M1',      'group': '🇪🇺 Europe Swaps',    'color': '#059669'},
    'AAHIM00': {'label': 'Propane CIF NWE Swap M2',      'group': '🇪🇺 Europe Swaps',    'color': '#10b981'},
    'AAHIO00': {'label': 'Propane CIF NWE Swap M3',      'group': '🇪🇺 Europe Swaps',    'color': '#34d399'},
    # ── EUROPE TIME SPREADS ──────────────────────────────────
    'PNM0102': {'label': 'Propane NWE M1/M2 Spread',     'group': '🇪🇺 Europe Spreads',  'color': '#6ee7b7'},
    'PNM0203': {'label': 'Propane NWE M2/M3 Spread',     'group': '🇪🇺 Europe Spreads',  'color': '#a7f3d0'},
    # ── EU CRACK / SWITCH ────────────────────────────────────
    'AAYJA00': {'label': 'Propane vs Naphtha NWE M1',    'group': '🇪🇺 EU LPG/Naphtha', 'color': '#d97706'},
    'AAYJB00': {'label': 'Propane vs Naphtha NWE M2',    'group': '🇪🇺 EU LPG/Naphtha', 'color': '#f59e0b'},

    # ── ASIA PHYSICAL ────────────────────────────────────────
    'AAVAK00': {'label': 'Propane CFR N.Asia 30-45d',    'group': '🌏 Asia Physical',    'color': '#ef4444'},
    'AAVAL00': {'label': 'Propane CFR N.Asia 45-60d',    'group': '🌏 Asia Physical',    'color': '#f87171'},
    'AAVAM00': {'label': 'Propane CFR N.Asia 60-75d',    'group': '🌏 Asia Physical',    'color': '#fca5a5'},
    # ── ASIA CASH DIFFS ──────────────────────────────────────
    'PMAAX00': {'label': 'Propane CFR N.Asia vs SCP M1', 'group': '🌏 Asia Cash Diff',   'color': '#dc2626'},
    'PMAAH00': {'label': 'Butane CFR N.Asia vs SCP M1',  'group': '🌏 Asia Cash Diff',   'color': '#b91c1c'},
    'AABAI00': {'label': 'Propane CFR S.China vs SCP',   'group': '🌏 Asia Cash Diff',   'color': '#991b1b'},

    # ── MIDDLE EAST ──────────────────────────────────────────
    'PMUDM00': {'label': 'Propane FOB Arab Gulf',        'group': '🌍 Middle East',      'color': '#7c3aed'},
    'PMUDR00': {'label': 'Butane FOB Arab Gulf',         'group': '🌍 Middle East',      'color': '#8b5cf6'},
    'PMABF00': {'label': 'Propane FOB AG vs Saudi CP',   'group': '🌍 ME Cash Diff',     'color': '#a78bfa'},
    'PMABG00': {'label': 'Butane FOB AG vs Saudi CP',    'group': '🌍 ME Cash Diff',     'color': '#c4b5fd'},

    # ── SAUDI CP ─────────────────────────────────────────────
    'AAHHG00': {'label': 'Saudi CP Propane Swap M1',     'group': '💡 Saudi CP',         'color': '#f59e0b'},
    'AAHHH00': {'label': 'Saudi CP Propane Swap M2',     'group': '💡 Saudi CP',         'color': '#fbbf24'},
    'AAHHI00': {'label': 'Saudi CP Propane Swap M3',     'group': '💡 Saudi CP',         'color': '#fcd34d'},

    # ── FREIGHT ──────────────────────────────────────────────
    'AAPNI00': {'label': 'VLGC PG → Japan 44kt',        'group': '🚢 Freight',          'color': '#64748b'},
    'AAPNH00': {'label': 'VLGC PG → E.China 44kt',      'group': '🚢 Freight',          'color': '#94a3b8'},
    'AAPNG00': {'label': 'VLGC PG → S.China 44kt',      'group': '🚢 Freight',          'color': '#cbd5e1'},
    'AAXIS00': {'label': 'VLGC Houston → Japan',         'group': '🚢 Freight',          'color': '#475569'},
    'AAXIQ00': {'label': 'VLGC Houston → NWE',           'group': '🚢 Freight',          'color': '#334155'},

    # ── NAPHTHA (LPG switch signal) ──────────────────────────
    'PAAAL00': {'label': 'Naphtha CIF NWE',              'group': '🛢️ Naphtha',          'color': '#78716c'},

    # ── TIME SPREADS ─────────────────────────────────────────
    'LPM0102': {'label': 'Propane USGC M1/M2 Spread',   'group': '📈 Time Spreads',     'color': '#ec4899'},
    'LPM0203': {'label': 'Propane USGC M2/M3 Spread',   'group': '📈 Time Spreads',     'color': '#f9a8d4'},
}

# ─────────────────────────────────────────────────────────────
# 2.  LOAD DATA FROM ATLAS
# ─────────────────────────────────────────────────────────────
LOOKBACK_DAYS = 365 * 3   # 3-year window; change to 90 for a quick view

ALL_TICKERS = list(TICKER_CONFIG.keys())
codes_str   = ','.join([f"'{c}'" for c in ALL_TICKERS])

df_raw = spark.sql(f"""
    SELECT
        publication_date,
        keys                   AS price_code,
        description,
        publisher_column_value AS price,
        atlas_column_name      AS price_type
    FROM ms_atlas.ms03price_standard.price_v1latest
    WHERE data_source = 'Platts'
      AND keys IN ({codes_str})
      AND atlas_column_name = 'CLOSE'
      AND publication_date >= DATEADD(day, -{LOOKBACK_DAYS}, current_date())
    ORDER BY publication_date, keys
""").toPandas()

df_raw['publication_date'] = pd.to_datetime(df_raw['publication_date'])
df_raw['price']            = pd.to_numeric(df_raw['price'], errors='coerce')

# Pivot → wide format: rows = date, columns = ticker
df = df_raw.pivot_table(
    index='publication_date',
    columns='price_code',
    values='price',
    aggfunc='last'
).sort_index()

# Latest date present
latest_date = df.index.max()
available   = [t for t in ALL_TICKERS if t in df.columns]

print(f"✅  {len(df)} trading days loaded")
print(f"📅  Range : {df.index.min().date()} → {latest_date.date()}")
print(f"📊  Series: {len(available)} / {len(ALL_TICKERS)} available")

# ─────────────────────────────────────────────────────────────
# 3.  HELPER UTILITIES
# ─────────────────────────────────────────────────────────────
CHART_THEME = dict(
    template='plotly_dark',
    paper_bgcolor='#0f172a',
    plot_bgcolor='#1e293b',
    font_color='#e2e8f0',
    font_family='Consolas, monospace',
)

def _pct_chg(col, periods):
    """% change over N business days, NaN if insufficient history."""
    if col not in df.columns:
        return np.nan
    s  = df[col].dropna()
    if len(s) <= periods:
        return np.nan
    return round((s.iloc[-1] / s.iloc[-1 - periods] - 1) * 100, 2)

def _abs_chg(col, periods):
    if col not in df.columns:
        return np.nan
    s  = df[col].dropna()
    if len(s) <= periods:
        return np.nan
    return round(s.iloc[-1] - s.iloc[-1 - periods], 2)

def arrow(val):
    if pd.isna(val):  return "—"
    return ("▲ " if val > 0 else "▼ ") + str(abs(val))

# ─────────────────────────────────────────────────────────────
# 4.  SECTION A — SUMMARY TABLE  (print first, every morning)
# ─────────────────────────────────────────────────────────────
rows = []
for ticker, meta in TICKER_CONFIG.items():
    if ticker not in df.columns:
        continue
    s = df[ticker].dropna()
    if s.empty:
        continue
    last_val = s.iloc[-1]
    rows.append({
        'Ticker' : ticker,
        'Description'  : meta['label'],
        'Group'        : meta['group'],
        'Latest'       : round(last_val, 2),
        '1D Chg'       : _abs_chg(ticker, 1),
        '1W Chg'       : _abs_chg(ticker, 5),
        '1M Chg'       : _abs_chg(ticker, 21),
        '1D %'         : _pct_chg(ticker, 1),
        '1M %'         : _pct_chg(ticker, 21),
        '52W High'     : round(df[ticker].rolling(252).max().iloc[-1], 2),
        '52W Low'      : round(df[ticker].rolling(252).min().iloc[-1], 2),
    })

summary = pd.DataFrame(rows).sort_values(['Group', 'Ticker'])

# Conditional formatting helper for display
def _color_cell(val):
    if isinstance(val, float) and not np.isnan(val):
        if val > 0:   return 'color: #4ade80'
        if val < 0:   return 'color: #f87171'
    return ''

styled = (
    summary.style
    .applymap(_color_cell, subset=['1D Chg','1W Chg','1M Chg','1D %','1M %'])
    .format({
        'Latest': '{:.2f}', '1D Chg': '{:+.2f}', '1W Chg': '{:+.2f}',
        '1M Chg': '{:+.2f}', '1D %':  '{:+.2f}%','1M %':   '{:+.2f}%',
        '52W High': '{:.2f}', '52W Low': '{:.2f}',
    }, na_rep='—')
    .set_table_styles([{
        'selector': 'th',
        'props': [('background-color','#1e293b'),('color','#94a3b8'),
                  ('font-family','Consolas,monospace'),('font-size','12px')]
    },{
        'selector': 'td',
        'props': [('background-color','#0f172a'),('color','#e2e8f0'),
                  ('font-family','Consolas,monospace'),('font-size','12px'),
                  ('border','1px solid #1e293b')]
    }])
    .hide(axis='index')
)

displayHTML(f"<h2 style='color:#e2e8f0;font-family:Consolas'>📊 LPG Market Snapshot — {latest_date.date()}</h2>")
display(styled)

# ─────────────────────────────────────────────────────────────
# 5.  SECTION B — CORE OUTRIGHTS  (US / Europe / Asia / ME)
# ─────────────────────────────────────────────────────────────
OUTRIGHT_GROUPS = {
    '🇺🇸 US':     ['PMAAY00', 'AAHYX00', 'AAHYY00', 'AAHYZ00'],
    '🇪🇺 Europe': ['PMABA00', 'PMAAS00', 'AAHIK00', 'AAHIM00', 'AAHIO00'],
    '🌏 Asia':    ['AAVAK00', 'AAVAL00', 'AAVAM00'],
    '🌍 ME/SCP':  ['PMUDM00', 'AAHHG00', 'AAHHH00', 'AAHHI00'],
}

fig_outrights = make_subplots(
    rows=2, cols=2,
    subplot_titles=list(OUTRIGHT_GROUPS.keys()),
    shared_xaxes=True,
    vertical_spacing=0.08,
    horizontal_spacing=0.06,
)

pos = {k: (r+1, c+1) for (k), (r, c) in
       zip(OUTRIGHT_GROUPS.keys(), [(0,0),(0,1),(1,0),(1,1)])}

for group, tickers in OUTRIGHT_GROUPS.items():
    row, col = pos[group]
    for t in tickers:
        if t not in df.columns:
            continue
        meta = TICKER_CONFIG.get(t, {})
        fig_outrights.add_trace(
            go.Scatter(
                x=df.index, y=df[t],
                name=meta.get('label', t),
                line=dict(color=meta.get('color','#94a3b8'), width=1.8),
                hovertemplate='%{x|%d %b %Y}  <b>%{y:.2f}</b><extra>' + meta.get('label',t) + '</extra>',
            ),
            row=row, col=col
        )

fig_outrights.update_layout(
    title=f"Core Outright Prices — {latest_date.date()}",
    height=650, **CHART_THEME,
    legend=dict(orientation='h', y=-0.15, font_size=10),
    hovermode='x unified',
)
fig_outrights.show()

# ─────────────────────────────────────────────────────────────
# 6.  SECTION C — FORWARD CURVE SNAPSHOT  (M1 / M2 / M3 bar)
# ─────────────────────────────────────────────────────────────
CURVE_TICKERS = {
    'US Propane':     [('AAHYX00','M1'), ('AAHYY00','M2'), ('AAHYZ00','M3')],
    'NWE Propane':    [('AAHIK00','M1'), ('AAHIM00','M2'), ('AAHIO00','M3')],
    'Saudi CP':       [('AAHHG00','M1'), ('AAHHH00','M2'), ('AAHHI00','M3')],
}

fig_curve = go.Figure()
colors_bar = {'M1': '#3b82f6', 'M2': '#60a5fa', 'M3': '#93c5fd'}

for market, pairs in CURVE_TICKERS.items():
    vals = []
    labels = []
    colors = []
    for ticker, tenor in pairs:
        if ticker in df.columns:
            v = df[ticker].dropna()
            vals.append(v.iloc[-1] if not v.empty else np.nan)
        else:
            vals.append(np.nan)
        labels.append(f"{market} {tenor}")
        colors.append(colors_bar[tenor])

    fig_curve.add_trace(go.Bar(
        name=market,
        x=[f"{market} {t}" for _, t in pairs],
        y=vals,
        text=[f"{v:.1f}" if not np.isnan(v) else "N/A" for v in vals],
        textposition='outside',
        marker_color=[colors_bar[t] for _, t in pairs],
    ))

fig_curve.update_layout(
    title=f"Forward Curve Snapshot (latest close) — {latest_date.date()}",
    yaxis_title='$/mt', height=420, **CHART_THEME,
    barmode='group',
    showlegend=True,
)
fig_curve.show()

# ─────────────────────────────────────────────────────────────
# 7.  SECTION D — CASH DIFFS & SPREADS (the arb signals)
# ─────────────────────────────────────────────────────────────
SPREAD_TICKERS = {
    '🌏 Asia Cash Diffs':  ['PMAAX00', 'PMAAH00', 'AABAI00', 'PMABF00'],
    '🇺🇸 US Arb / Export': ['AAXIO00', 'LPM0102', 'LPM0203'],
    '🇪🇺 EU Switch Signal': ['AAYJA00', 'AAYJB00', 'PNM0102', 'PNM0203'],
}

fig_spreads = make_subplots(
    rows=1, cols=3,
    subplot_titles=list(SPREAD_TICKERS.keys()),
    shared_xaxes=True,
    horizontal_spacing=0.07,
)

for col_idx, (group, tickers) in enumerate(SPREAD_TICKERS.items(), 1):
    for t in tickers:
        if t not in df.columns:
            continue
        meta = TICKER_CONFIG.get(t, {})
        fig_spreads.add_trace(
            go.Scatter(
                x=df.index, y=df[t],
                name=meta.get('label', t),
                line=dict(color=meta.get('color','#94a3b8'), width=1.6),
                hovertemplate='%{x|%d %b %Y}  <b>%{y:.2f}</b><extra>' + meta.get('label',t) + '</extra>',
            ),
            row=1, col=col_idx,
        )
    # Zero line for context
    fig_spreads.add_hline(y=0, line_dash='dot', line_color='#475569',
                          line_width=1, row=1, col=col_idx)

fig_spreads.update_layout(
    title=f"Spreads & Arb Signals — {latest_date.date()}",
    height=420, **CHART_THEME,
    legend=dict(orientation='h', y=-0.2, font_size=10),
    hovermode='x unified',
)
fig_spreads.show()

# ─────────────────────────────────────────────────────────────
# 8.  SECTION E — FREIGHT  (the option cost)
# ─────────────────────────────────────────────────────────────
FREIGHT_TICKERS = ['AAPNI00', 'AAPNH00', 'AAPNG00', 'AAXIS00', 'AAXIQ00']

fig_freight = go.Figure()
for t in FREIGHT_TICKERS:
    if t not in df.columns:
        continue
    meta = TICKER_CONFIG[t]
    fig_freight.add_trace(go.Scatter(
        x=df.index, y=df[t],
        name=meta['label'],
        line=dict(color=meta['color'], width=1.8),
        hovertemplate='%{x|%d %b %Y}  <b>%{y:.2f}</b><extra>' + meta['label'] + '</extra>',
    ))

fig_freight.update_layout(
    title=f"VLGC Freight ($/mt) — {latest_date.date()}",
    yaxis_title='$/mt', height=380, **CHART_THEME,
    legend=dict(orientation='h', y=-0.2),
    hovermode='x unified',
)
fig_freight.show()

# ─────────────────────────────────────────────────────────────
# 9.  SECTION F — ROLLING CORRELATION HEATMAP  (90d)
#     Useful to see how spreads / regions move together
# ─────────────────────────────────────────────────────────────
CORR_TICKERS = [
    'PMAAY00','AAHYX00',        # US
    'PMABA00','AAHIK00',        # NWE
    'AAVAK00','PMAAX00',        # Asia / cash diff
    'PMUDM00','AAHHG00',        # ME / Saudi CP
    'AAPNI00','AAXIS00',        # Freight
    'PAAAL00',                  # Naphtha
    'LPM0102',                  # Time spread
]
corr_cols = [t for t in CORR_TICKERS if t in df.columns]
corr_labels = [TICKER_CONFIG[t]['label'] for t in corr_cols]

corr_df = df[corr_cols].tail(90).corr().round(2)

fig_corr = go.Figure(go.Heatmap(
    z=corr_df.values,
    x=corr_labels,
    y=corr_labels,
    colorscale='RdYlGn',
    zmin=-1, zmax=1,
    text=corr_df.values.round(2),
    texttemplate='%{text}',
    textfont_size=9,
    hovertemplate='%{y} / %{x}: <b>%{z}</b><extra></extra>',
))
fig_corr.update_layout(
    title='90-Day Rolling Correlation',
    height=520, **CHART_THEME,
    xaxis=dict(tickfont_size=9, tickangle=-35),
    yaxis=dict(tickfont_size=9),
)
fig_corr.show()

# ─────────────────────────────────────────────────────────────
# 10. SECTION G — SINGLE-TICKER DEEP DIVE  (reuse any morning)
# ─────────────────────────────────────────────────────────────
def deep_dive(ticker: str, lookback_days: int = 252):
    """Interactive OHLC-style chart with 20d/60d moving averages."""
    if ticker not in df_raw['price_code'].values:
        print(f"❌ {ticker} not found in dataset")
        return

    # Get CLOSE + HIGH + LOW if available
    sub = df_raw[df_raw['price_code'] == ticker].copy()
    sub = sub[sub['publication_date'] >= latest_date - pd.Timedelta(days=lookback_days * 1.5)]

    close = sub[sub['price_type'] == 'CLOSE'].set_index('publication_date')['price']
    high  = sub[sub['price_type'] == 'HIGH'].set_index('publication_date')['price']
    low   = sub[sub['price_type'] == 'LOW'].set_index('publication_date')['price']

    label = TICKER_CONFIG.get(ticker, {}).get('label', ticker)
    color = TICKER_CONFIG.get(ticker, {}).get('color', '#3b82f6')

    fig = go.Figure()

    # HL band
    if not high.empty and not low.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([high.index.to_series(), low.index.to_series()[::-1]]),
            y=pd.concat([high, low[::-1]]),
            fill='toself', fillcolor='rgba(100,130,180,0.12)',
            line=dict(width=0), name='High-Low band', showlegend=True,
        ))

    # Close line
    fig.add_trace(go.Scatter(
        x=close.index, y=close,
        name='Close', line=dict(color=color, width=2),
    ))

    # MAs
    for w, c in [(20, '#fbbf24'), (60, '#f87171')]:
        ma = close.rolling(w).mean()
        fig.add_trace(go.Scatter(
            x=ma.index, y=ma,
            name=f'{w}d MA', line=dict(color=c, width=1, dash='dot'),
        ))

    fig.update_layout(
        title=f"{label} ({ticker}) — deep dive",
        yaxis_title='$/mt', height=450, **CHART_THEME,
        legend=dict(orientation='h', y=-0.15),
        hovermode='x unified',
    )
    fig.show()

# Usage example — change ticker as needed:
deep_dive('PMAAX00')   # Propane CFR N.Asia vs Saudi CP  ← MAIN SIGNAL

# ─────────────────────────────────────────────────────────────
# 11. EXPORT TO CSV  (for Power BI ingestion)
# ─────────────────────────────────────────────────────────────
# Uncomment and adjust path when ready to connect to Power BI

# EXPORT_PATH = '/dbfs/mnt/your-storage/lpg_daily_export.csv'
# df.reset_index().rename(columns={'publication_date': 'Date'}).to_csv(
#     EXPORT_PATH, index=False
# )
# print(f"📤 Exported to {EXPORT_PATH}")
#
# For Power BI: connect via "Azure Databricks" connector or schedule
# this notebook as a Job and write to Azure Blob / ADLS Gen2.
# Then use Power BI's "Dataflow" or direct Blob connector.
