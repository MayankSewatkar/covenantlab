import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict
from pathlib import Path

def generate_synthetic_dataset(n: int = 200, path: str = "data/synthetic_deals.csv") -> pd.DataFrame:
    np.random.seed(42)
    scores = np.random.uniform(20, 95, n)
    spread_at_issue = 400 + np.random.normal(0, 80, n)
    spread_change = -0.8 * scores + np.random.normal(0, 30, n)
    price_12m = 95 + 0.05 * scores + np.random.normal(0, 5, n)
    default_prob = 1 / (1 + np.exp(0.1 * (scores - 50)))
    defaulted = np.random.binomial(1, default_prob, n)
    recovery = np.where(defaulted, np.random.uniform(20, 60, n), np.nan)

    df = pd.DataFrame({
        "deal_id": [f"DEAL_{i:04d}" for i in range(n)],
        "covenant_score": scores.round(2),
        "spread_at_issue": spread_at_issue.round(0),
        "spread_12m": (spread_at_issue + spread_change).round(0),
        "price_12m": price_12m.round(2),
        "defaulted": defaulted,
        "recovery_rate": recovery.round(2),
    })

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df

def run_backtest(dataset_path: str) -> Dict:
    if not Path(dataset_path).exists():
        generate_synthetic_dataset(path=dataset_path)

    df = pd.read_csv(dataset_path)
    df["spread_change"] = df["spread_12m"] - df["spread_at_issue"]
    df["quartile"] = pd.qcut(
        df["covenant_score"], q=4,
        labels=["Q1 Weakest", "Q2", "Q3", "Q4 Strongest"]
    )

    quartile_stats = df.groupby("quartile", observed=True).agg(
        n_deals=("deal_id", "count"),
        avg_score=("covenant_score", "mean"),
        avg_spread_change=("spread_change", "mean"),
        avg_price_12m=("price_12m", "mean"),
        default_rate=("defaulted", "mean"),
        avg_recovery=("recovery_rate", "mean"),
    ).reset_index().round(2).to_dict(orient="records")

    clean = df.dropna(subset=["covenant_score", "spread_change"])
    r, p = stats.pearsonr(clean["covenant_score"], clean["spread_change"])
    slope, intercept, _, p_val, _ = stats.linregress(
        clean["covenant_score"], clean["spread_change"]
    )

    regression = {
        "pearson_r": round(r, 4),
        "p_value": round(p, 4),
        "ols_slope": round(slope, 4),
        "ols_intercept": round(intercept, 4),
        "r_squared": round(r**2, 4),
        "n": len(clean),
        "significant": bool(p_val < 0.05),
    }

    return {
        "quartile_summary": quartile_stats,
        "regression": regression,
        "sample_size": len(df),
    }
