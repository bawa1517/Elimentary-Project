import pandas as pd


def load_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.drop_duplicates()

    num_cols = [
        "person_age",
        "person_income",
        "person_emp_exp",
        "loan_amnt",
        "loan_int_rate",
        "loan_percent_income",
        "cb_person_cred_hist_length",
        "credit_score",
    ]
    cat_cols = [
        "person_gender",
        "person_education",
        "person_home_ownership",
        "loan_intent",
        "previous_loan_defaults_on_file",
    ]

    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    for c in cat_cols:
        mode = df[c].mode()
        df[c] = df[c].fillna(mode.iloc[0] if not mode.empty else "unknown")

    y = df["loan_status"].copy()
    if not pd.api.types.is_numeric_dtype(y):
        m = {
            "default": 1,
            "defaulter": 1,
            "charged off": 1,
            "yes": 1,
            "y": 1,
            "true": 1,
            "1": 1,
            "no": 0,
            "n": 0,
            "false": 0,
            "0": 0,
            "paid": 0,
            "current": 0,
        }
        y = y.astype(str).str.lower().map(m).fillna(pd.to_numeric(y, errors="coerce")).fillna(0).astype(int)
    df["loan_status"] = y
    return df

