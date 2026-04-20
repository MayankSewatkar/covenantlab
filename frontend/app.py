import streamlit as st
import requests
import json
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="CovenantLab", page_icon="📋", layout="wide")
st.title("📋 CovenantLab — Credit Agreement Analyzer")
st.caption("Upload a credit agreement to extract, score, and analyze covenant strength.")

tab1, tab2, tab3 = st.tabs(["Analyze Agreement", "Backtest Data", "Raw Scorer"])

# ── Tab 1: File Upload ──────────────────────────────────────────────────────
with tab1:
    uploaded = st.file_uploader("Upload Credit Agreement", type=["pdf", "txt"])

    if uploaded:
        st.info(f"File loaded: **{uploaded.name}** ({len(uploaded.getvalue()):,} bytes)")
        if st.button("Analyze Covenants", type="primary"):
            with st.spinner("Extracting and scoring covenants via Claude..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/analyze",
                        files={"file": (uploaded.name, uploaded.getvalue())},
                        timeout=300
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            scoring = data["scoring"]

            # ── Score summary ──
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Overall Score", f"{scoring['overall_score']:.1f} / 100")
            col2.metric("Grade", scoring["grade"].split("—")[0].strip())
            col3.metric("Clauses Found", data["clause_count"])

            if scoring["missing_clauses"]:
                st.warning(
                    "Missing clauses (scored 0): "
                    + ", ".join(c.replace("_", " ").title() for c in scoring["missing_clauses"])
                )

            # ── Per-clause bar chart ──
            st.subheader("Clause Scores")
            clause_df = pd.DataFrame([
                {"Clause": k.replace("_", " ").title(), "Score": v}
                for k, v in scoring["clause_scores"].items()
            ])
            st.bar_chart(clause_df.set_index("Clause"), color="#4a90d9")

            # ── Risk flags summary ──
            st.subheader("Risk Flags")
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
                flags_df = pd.DataFrame(all_flags)
                st.dataframe(flags_df, use_container_width=True, hide_index=True)
            else:
                st.success("No major risk flags detected.")

            # ── Full covenant detail ──
            st.subheader("Extracted Covenants (Detail)")
            for cov in data["covenants"]:
                label = cov["clause_type"].replace("_", " ").title()
                score = cov.get("risk_score", "N/A")
                conf = cov.get("confidence", 0)
                with st.expander(f"{label} — Score: {score}  |  Confidence: {conf:.0%}"):
                    st.json(cov)

            # ── Raw JSON download ──
            st.download_button(
                "Download Full JSON",
                data=json.dumps(data, indent=2),
                file_name="covenant_analysis.json",
                mime="application/json"
            )

# ── Tab 2: Backtest ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("Backtest: Covenant Score vs Market Outcomes")
    st.caption("Synthetic dataset of 200 deals. Higher covenant score → better outcomes.")

    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            try:
                resp = requests.get(f"{API_URL}/backtest", timeout=30)
                resp.raise_for_status()
                bt = resp.json()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        qdf = pd.DataFrame(bt["quartile_summary"])
        st.dataframe(qdf, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        col1.bar_chart(qdf.set_index("quartile")["default_rate"], color="#e05c5c")
        col2.bar_chart(qdf.set_index("quartile")["avg_spread_change"], color="#4a90d9")

        reg = bt["regression"]
        st.subheader("Regression: Covenant Score → Spread Change")
        st.write(f"**Pearson r:** {reg['pearson_r']}  |  **p-value:** {reg['p_value']}  |  "
                 f"**R²:** {reg['r_squared']}  |  **Significant:** {reg['significant']}")

# ── Tab 3: Raw Text Scorer ──────────────────────────────────────────────────
with tab3:
    st.subheader("Quick Clause Scorer")
    st.caption("Paste raw clause text to score without uploading a full document.")

    clause_type = st.selectbox("Clause Type", [
        "debt_incurrence", "restricted_payments", "asset_sales",
        "collateral_guarantees", "amendment_voting"
    ])
    raw_text = st.text_area("Paste clause text here", height=200)

    if st.button("Score Clause", type="primary") and raw_text.strip():
        with st.spinner("Scoring..."):
            try:
                resp = requests.post(
                    f"{API_URL}/score-text",
                    json={"clauses": [{"clause_type": clause_type, "raw_text": raw_text}]},
                    timeout=60
                )
                result = resp.json()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        scoring = result["scoring"]
        st.metric("Clause Score", f"{scoring['overall_score']:.1f} / 100")
        st.metric("Grade", scoring["grade"])
        st.json(result["covenants"][0])
