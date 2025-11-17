import pandas as pd


def add_ecl(df: pd.DataFrame) -> pd.DataFrame:
    lgd_map = {"education": 0.3, "business": 0.5, "medical": 0.4, "venture": 0.6}
    df["lgd"] = df["loan_intent"].astype(str).str.lower().map(lgd_map).fillna(0.45)
    df["ead"] = df["loan_amnt"].clip(lower=0)
    df["ecl"] = df["pd"] * df["lgd"] * df["ead"]
    return df


def action_rule(ecl: float, med: float) -> str:
    if ecl > 1.5 * med:
        return "Reduce disbursement"
    if ecl > 1.1 * med:
        return "Increase interest rate"
    return "Monitor"


def aggregate(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    g = (
        df.groupby(["loan_intent", "person_gender"])
        .agg(pd_mean=("pd", "mean"), lgd=("lgd", "mean"), ecl=("ecl", "sum"))
        .reset_index()
    )
    med = g["ecl"].median() if not g.empty else 0.0
    g["action"] = [action_rule(v, med) for v in g["ecl"]]
    return g, med

