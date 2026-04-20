import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="CovenantLab",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Dark base */
  .stApp { background: #0d1117; color: #e6edf3; }
  section[data-testid="stSidebar"] { background: #161b22; }

  /* Hide default Streamlit header chrome */
  #MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }

  /* Tab strip */
  .stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #30363d;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #8b949e;
    border-radius: 7px;
    padding: 8px 20px;
    font-weight: 500;
    font-size: 0.875rem;
    border: none;
  }
  .stTabs [aria-selected="true"] {
    background: #1f6feb !important;
    color: #ffffff !important;
  }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
  }
  [data-testid="metric-container"] label {
    color: #8b949e !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
  }

  /* Primary button */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: opacity 0.15s;
  }
  .stButton > button[kind="primary"]:hover { opacity: 0.85; }

  /* Secondary button */
  .stButton > button {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 28px;
    font-weight: 500;
    font-size: 0.9rem;
    transition: background 0.15s;
  }
  .stButton > button:hover { background: #30363d; }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background: #161b22;
    border: 2px dashed #30363d;
    border-radius: 12px;
    padding: 24px;
  }
  [data-testid="stFileUploader"]:hover { border-color: #1f6feb; }

  /* Expander */
  [data-testid="stExpander"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
  }
  [data-testid="stExpander"] summary { color: #e6edf3; font-weight: 500; }

  /* Dataframe */
  [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

  /* Divider */
  hr { border-color: #21262d; }

  /* Alerts */
  [data-testid="stAlert"] { border-radius: 10px; border-left-width: 4px; }

  /* Selectbox / text area */
  [data-testid="stSelectbox"] > div > div,
  textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
  }

  /* Download button */
  .stDownloadButton > button {
    background: #21262d;
    color: #58a6ff;
    border: 1px solid #30363d;
    border-radius: 8px;
    font-weight: 500;
  }
  .stDownloadButton > button:hover { background: #30363d; }

  /* Custom card */
  .cl-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
  }
  .cl-card-accent { border-left: 4px solid #1f6feb; }
  .cl-card h4 { margin: 0 0 6px 0; color: #e6edf3; font-size: 0.95rem; font-weight: 600; }
  .cl-card p  { margin: 0; color: #8b949e; font-size: 0.85rem; }

  /* Score badge */
  .score-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
  }
  .score-high   { background: #1a3a2a; color: #3fb950; border: 1px solid #238636; }
  .score-mid    { background: #3a2a10; color: #e3b341; border: 1px solid #9e6a03; }
  .score-low    { background: #3a1a1a; color: #f85149; border: 1px solid #da3633; }

  /* Severity pill */
  .pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.05em;
  }
  .pill-high   { background: #3a1a1a; color: #f85149; }
  .pill-medium { background: #3a2a10; color: #e3b341; }
  .pill-low    { background: #1a2a1a; color: #3fb950; }

  /* Stat row */
  .stat-row {
    display: flex; gap: 16px; flex-wrap: wrap; margin: 8px 0;
  }
  .stat-item {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 10px 16px;
    flex: 1; min-width: 120px;
  }
  .stat-item .label { font-size: 0.72rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; }
  .stat-item .value { font-size: 1.1rem; font-weight: 700; color: #e6edf3; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 28px 0 20px 0; border-bottom: 1px solid #21262d; margin-bottom: 28px;">
  <div style="display:flex; align-items:center; gap:14px;">
    <div style="background: linear-gradient(135deg,#1f6feb,#388bfd); border-radius:12px;
                width:44px; height:44px; display:flex; align-items:center; justify-content:center;
                font-size:22px;">⚖️</div>
    <div>
      <div style="font-size:1.5rem; font-weight:700; color:#e6edf3; letter-spacing:-0.02em;">CovenantLab</div>
      <div style="font-size:0.82rem; color:#8b949e; margin-top:1px;">Credit Agreement Intelligence Platform</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def score_class(s):
    if s >= 70: return "score-high"
    if s >= 40: return "score-mid"
    return "score-low"


def severity_pill(sev: str) -> str:
    s = sev.lower()
    cls = "pill-high" if s == "high" else ("pill-medium" if s == "medium" else "pill-low")
    return f'<span class="pill {cls}">{sev.upper()}</span>'


tab1, tab2, tab3 = st.tabs(["  Analyze Agreement  ", "  Backtest Data  ", "  Raw Scorer  "])


# ── Tab 1: File Upload ───────────────────────────────────────────────────────
with tab1:
    col_up, col_info = st.columns([3, 2], gap="large")

    with col_up:
        st.markdown("#### Upload Credit Agreement")
        uploaded = st.file_uploader(
            "Drag and drop a PDF or TXT file",
            type=["pdf", "txt"],
            label_visibility="collapsed",
        )

    with col_info:
        st.markdown("""
        <div class="cl-card cl-card-accent" style="margin-top:28px;">
          <h4>What gets analyzed</h4>
          <p>Debt incurrence · Restricted payments · Asset sales<br>
             Collateral & guarantees · Amendment voting thresholds</p>
        </div>
        <div class="cl-card">
          <h4>Scoring methodology</h4>
          <p>Each covenant is evaluated for tightness, carve-outs,
             basket sizes, and lender protections by Claude AI.</p>
        </div>
        """, unsafe_allow_html=True)

    if uploaded:
        size_kb = len(uploaded.getvalue()) / 1024
        st.markdown(f"""
        <div class="cl-card" style="display:flex; align-items:center; gap:14px; margin-top:8px;">
          <span style="font-size:1.6rem;">📄</span>
          <div>
            <div style="font-weight:600; color:#e6edf3;">{uploaded.name}</div>
            <div style="font-size:0.8rem; color:#8b949e;">{size_kb:.1f} KB · ready to analyze</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Analyze Covenants", type="primary"):
            with st.spinner("Extracting and scoring covenants via Claude..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/analyze",
                        files={"file": (uploaded.name, uploaded.getvalue())},
                        timeout=300,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            scoring = data["scoring"]
            overall = scoring["overall_score"]
            grade = scoring["grade"].split("—")[0].strip()

            st.markdown("<hr style='margin:28px 0'>", unsafe_allow_html=True)

            # Score hero
            sc = score_class(overall)
            st.markdown(f"""
            <div class="cl-card" style="display:flex; align-items:center; gap:32px; padding:28px 32px;">
              <div>
                <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase;
                            letter-spacing:.06em; margin-bottom:6px;">Overall Covenant Score</div>
                <span class="score-badge {sc}" style="font-size:2.4rem; padding:8px 24px;">
                  {overall:.1f}
                </span>
              </div>
              <div style="width:1px; background:#30363d; height:60px;"></div>
              <div>
                <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase;
                            letter-spacing:.06em; margin-bottom:6px;">Grade</div>
                <div style="font-size:1.5rem; font-weight:700; color:#e6edf3;">{grade}</div>
              </div>
              <div style="width:1px; background:#30363d; height:60px;"></div>
              <div>
                <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase;
                            letter-spacing:.06em; margin-bottom:6px;">Clauses Found</div>
                <div style="font-size:1.5rem; font-weight:700; color:#e6edf3;">{data['clause_count']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if scoring["missing_clauses"]:
                missing = ", ".join(c.replace("_", " ").title() for c in scoring["missing_clauses"])
                st.warning(f"Missing clauses (scored 0): {missing}")

            # Clause scores chart
            st.markdown("#### Clause Scores")
            clause_df = pd.DataFrame([
                {"Clause": k.replace("_", " ").title(), "Score": v}
                for k, v in scoring["clause_scores"].items()
            ])
            colors = ["#3fb950" if v >= 70 else "#e3b341" if v >= 40 else "#f85149"
                      for v in clause_df["Score"]]
            fig = go.Figure(go.Bar(
                x=clause_df["Score"],
                y=clause_df["Clause"],
                orientation="h",
                marker_color=colors,
                text=[f"{v:.0f}" for v in clause_df["Score"]],
                textposition="outside",
                textfont=dict(color="#8b949e", size=12),
            ))
            fig.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font=dict(family="Inter", color="#8b949e"),
                margin=dict(l=0, r=40, t=8, b=0),
                height=240,
                xaxis=dict(range=[0, 110], showgrid=True, gridcolor="#21262d",
                           tickfont=dict(color="#8b949e"), zeroline=False),
                yaxis=dict(showgrid=False, tickfont=dict(color="#e6edf3", size=13)),
                bargap=0.35,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Risk flags
            st.markdown("#### Risk Flags")
            all_flags = []
            for cov in data["covenants"]:
                for flag in cov.get("risk_flags") or []:
                    all_flags.append({
                        "Clause": cov["clause_type"].replace("_", " ").title(),
                        "Flag": flag.get("flag", ""),
                        "Severity": flag.get("severity", "").upper(),
                        "Rationale": flag.get("rationale", ""),
                    })

            if all_flags:
                for f in all_flags:
                    pill = severity_pill(f["Severity"])
                    st.markdown(f"""
                    <div class="cl-card" style="margin-bottom:8px;">
                      <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                        {pill}
                        <span style="font-size:0.78rem; color:#8b949e; font-weight:500;">{f['Clause']}</span>
                      </div>
                      <div style="font-weight:600; color:#e6edf3; font-size:0.9rem;">{f['Flag']}</div>
                      <div style="color:#8b949e; font-size:0.82rem; margin-top:3px;">{f['Rationale']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No major risk flags detected.")

            # Covenant detail expanders
            st.markdown("#### Extracted Covenants")
            for cov in data["covenants"]:
                label = cov["clause_type"].replace("_", " ").title()
                score = cov.get("risk_score", "N/A")
                conf = cov.get("confidence", 0)
                sc2 = score_class(score) if isinstance(score, (int, float)) else "score-mid"
                with st.expander(f"{label}  ·  Score {score}  ·  {conf:.0%} confidence"):
                    st.json(cov)

            st.download_button(
                "⬇  Download Full JSON",
                data=json.dumps(data, indent=2),
                file_name="covenant_analysis.json",
                mime="application/json",
            )


# ── Tab 2: Backtest ──────────────────────────────────────────────────────────
with tab2:
    col_h, col_btn = st.columns([5, 1])
    with col_h:
        st.markdown("#### Backtest: Covenant Score vs Market Outcomes")
        st.markdown('<p style="color:#8b949e; font-size:0.85rem; margin-top:-8px;">Synthetic dataset of 200 deals — higher covenant score → better market outcomes.</p>', unsafe_allow_html=True)
    with col_btn:
        run = st.button("Run Backtest", type="primary")

    if run:
        with st.spinner("Running backtest..."):
            try:
                resp = requests.get(f"{API_URL}/backtest", timeout=30)
                resp.raise_for_status()
                bt = resp.json()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        qdf = pd.DataFrame(bt["quartile_summary"])
        reg = bt["regression"]

        # Regression stat cards
        sig_color = "#3fb950" if reg["significant"] else "#f85149"
        sig_label = "Significant" if reg["significant"] else "Not Significant"
        st.markdown(f"""
        <div class="stat-row" style="margin-bottom:24px;">
          <div class="stat-item"><div class="label">Pearson r</div><div class="value">{reg['pearson_r']}</div></div>
          <div class="stat-item"><div class="label">R²</div><div class="value">{reg['r_squared']}</div></div>
          <div class="stat-item"><div class="label">p-value</div><div class="value">{reg['p_value']}</div></div>
          <div class="stat-item"><div class="label">OLS Slope</div><div class="value">{reg['ols_slope']}</div></div>
          <div class="stat-item"><div class="label">n</div><div class="value">{reg['n']}</div></div>
          <div class="stat-item">
            <div class="label">Significance</div>
            <div class="value" style="color:{sig_color}; font-size:0.9rem;">{sig_label}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Charts side by side
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div style="font-size:0.85rem; color:#8b949e; margin-bottom:8px; font-weight:600;">DEFAULT RATE BY QUARTILE</div>', unsafe_allow_html=True)
            fig1 = go.Figure(go.Bar(
                x=qdf["quartile"],
                y=qdf["default_rate"],
                marker_color=["#f85149", "#e3b341", "#58a6ff", "#3fb950"],
                text=[f"{v:.0%}" for v in qdf["default_rate"]],
                textposition="outside",
                textfont=dict(color="#8b949e", size=11),
            ))
            fig1.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font=dict(family="Inter", color="#8b949e"),
                margin=dict(l=0, r=0, t=8, b=0), height=280,
                xaxis=dict(showgrid=False, tickfont=dict(color="#e6edf3")),
                yaxis=dict(showgrid=True, gridcolor="#21262d", tickformat=".0%",
                           tickfont=dict(color="#8b949e"), zeroline=False),
                bargap=0.35,
            )
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        with col2:
            st.markdown('<div style="font-size:0.85rem; color:#8b949e; margin-bottom:8px; font-weight:600;">AVG SPREAD CHANGE (bps) BY QUARTILE</div>', unsafe_allow_html=True)
            fig2 = go.Figure(go.Bar(
                x=qdf["quartile"],
                y=qdf["avg_spread_change"],
                marker_color=["#f85149", "#e3b341", "#58a6ff", "#3fb950"],
                text=[f"{v:+.0f}" for v in qdf["avg_spread_change"]],
                textposition="outside",
                textfont=dict(color="#8b949e", size=11),
            ))
            fig2.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font=dict(family="Inter", color="#8b949e"),
                margin=dict(l=0, r=0, t=8, b=0), height=280,
                xaxis=dict(showgrid=False, tickfont=dict(color="#e6edf3")),
                yaxis=dict(showgrid=True, gridcolor="#21262d", ticksuffix=" bps",
                           tickfont=dict(color="#8b949e"), zeroline=False),
                bargap=0.35,
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # Scatter: score vs spread change
        raw_df = pd.DataFrame({
            "Covenant Score": [r["avg_score"] for r in bt["quartile_summary"]],
            "Avg Spread Change": qdf["avg_spread_change"],
            "Quartile": qdf["quartile"],
        })
        st.markdown('<div style="font-size:0.85rem; color:#8b949e; margin: 16px 0 8px 0; font-weight:600;">QUARTILE SUMMARY TABLE</div>', unsafe_allow_html=True)
        st.dataframe(
            qdf.rename(columns={
                "quartile": "Quartile", "n_deals": "Deals",
                "avg_score": "Avg Score", "avg_spread_change": "Spread Δ (bps)",
                "avg_price_12m": "Price @ 12m", "default_rate": "Default Rate",
                "avg_recovery": "Avg Recovery",
            }),
            use_container_width=True, hide_index=True,
        )


# ── Tab 3: Raw Scorer ────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### Quick Clause Scorer")
    st.markdown('<p style="color:#8b949e; font-size:0.85rem; margin-top:-8px;">Paste raw clause text to score a single covenant without uploading a full document.</p>', unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        clause_type = st.selectbox(
            "Clause Type",
            ["debt_incurrence", "restricted_payments", "asset_sales",
             "collateral_guarantees", "amendment_voting"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        raw_text = st.text_area("Paste clause text", height=220, placeholder="Paste the covenant language here...")

        if st.button("Score Clause", type="primary") and raw_text.strip():
            with st.spinner("Scoring via Claude..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/score-text",
                        json={"clauses": [{"clause_type": clause_type, "raw_text": raw_text}]},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            scoring = result["scoring"]
            overall = scoring["overall_score"]
            sc = score_class(overall)

            with col_right:
                st.markdown(f"""
                <div class="cl-card" style="margin-top:28px; text-align:center; padding:32px;">
                  <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase;
                              letter-spacing:.06em; margin-bottom:10px;">Clause Score</div>
                  <span class="score-badge {sc}" style="font-size:2.8rem; padding:10px 28px;">
                    {overall:.1f}
                  </span>
                  <div style="margin-top:14px; font-size:1.1rem; font-weight:600; color:#e6edf3;">
                    {scoring['grade']}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                cov = result["covenants"][0]
                flags = cov.get("risk_flags") or []
                if flags:
                    st.markdown("**Risk Flags**")
                    for f in flags:
                        st.markdown(f"{severity_pill(f.get('severity',''))} {f.get('flag','')}", unsafe_allow_html=True)
                        st.caption(f.get("rationale", ""))
                else:
                    st.success("No risk flags.")

                with st.expander("Full JSON"):
                    st.json(cov)

    with col_right:
        st.markdown("""
        <div class="cl-card cl-card-accent" style="margin-top:28px;">
          <h4>Scoring criteria</h4>
          <p>Tightness of restrictions · Size and breadth of carve-outs ·
             Basket headroom · Cross-default triggers · Lender consent thresholds</p>
        </div>
        <div class="cl-card">
          <h4>Score interpretation</h4>
          <p>
            <span style="color:#3fb950; font-weight:600;">70–100</span> Strong protections<br>
            <span style="color:#e3b341; font-weight:600;">40–69</span>&nbsp; Moderate — review carve-outs<br>
            <span style="color:#f85149; font-weight:600;">0–39</span>&nbsp;&nbsp; Weak — material lender risk
          </p>
        </div>
        """, unsafe_allow_html=True)
