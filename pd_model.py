from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import pandas as pd


def build_pd(df: pd.DataFrame) -> pd.Series:
    X_cols = [
        "person_age",
        "person_income",
        "person_emp_exp",
        "loan_amnt",
        "loan_int_rate",
        "loan_percent_income",
        "cb_person_cred_hist_length",
        "credit_score",
        "person_gender",
        "person_education",
        "person_home_ownership",
        "loan_intent",
        "previous_loan_defaults_on_file",
    ]
    X = df[X_cols]
    y = df["loan_status"].astype(int)
    cat = [
        "person_gender",
        "person_education",
        "person_home_ownership",
        "loan_intent",
        "previous_loan_defaults_on_file",
    ]
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), cat)], remainder="passthrough")
    clf = LogisticRegression(class_weight="balanced", max_iter=500)
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    pipe.fit(X, y)
    pd_hat = pipe.predict_proba(X)[:, 1]
    return pd.Series(pd_hat, index=df.index, name="pd")

