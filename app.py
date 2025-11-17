import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from data import load_clean
from pd_model import build_pd
from ecl import add_ecl, aggregate
from ai import get_insight
from storage import save_report, list_reports, load_report, save_insight, list_insights, update_insight

st.set_page_config(page_title="ECL Dashboard", layout="centered")


@st.cache_data(show_spinner=False)
def run_model_and_metrics() -> pd.DataFrame:
    df = load_clean("loan_data.csv")
    df["pd"] = build_pd(df)
    df = add_ecl(df)
    return df


def action_rule(ecl: float, med: float) -> str:
    if ecl > 1.5 * med:
        return "Reduce disbursement"
    if ecl > 1.1 * med:
        return "Increase interest rate"
    return "Monitor"


def main():
    st.title("Expected Credit Loss (ECL) Dashboard")
    df = run_model_and_metrics()

    intents = sorted(df["loan_intent"].unique().tolist())
    genders = sorted(df["person_gender"].unique().tolist())

    st.sidebar.header("Filters")
    sel_intent = st.sidebar.multiselect("Loan intent", intents, default=intents)
    sel_gender = st.sidebar.multiselect("Gender", genders, default=genders)

    f = df[df["loan_intent"].isin(sel_intent) & df["person_gender"].isin(sel_gender)]
    if f.empty:
        st.warning("No data for current selections.")
        return

    g, med = aggregate(f)

    st.subheader("Summary")
    st.dataframe(g.round({"pd_mean": 4, "lgd": 3, "ecl": 2}))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save ECL report", use_container_width=True):
            rid = save_report(g, med)
            st.success(f"Report saved: {rid}")
            st.session_state["last_rid"] = rid
    with col2:
        note = st.text_area("Analyst insight", placeholder="Short note for audit", height=80)
        rec = st.selectbox("Recommendation", ["Monitor", "Increase interest rate", "Reduce disbursement"])
        if st.button("Save insight", use_container_width=True):
            rid = st.session_state.get("last_rid", pd.Timestamp.now().strftime("%Y%m%d_%H%M%S"))
            iid = save_insight(rid, note, rec)
            st.success(f"Insight saved: {iid}")

    st.subheader("ECL by Gender")
    by_gender = f.groupby("person_gender")["ecl"].sum()
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(by_gender.index.astype(str), by_gender.values, color="#4c72b0")
    ax.set_ylabel("ECL")
    ax.set_xlabel("Gender")
    ax.set_title("ECL by Gender")
    st.pyplot(fig, clear_figure=True)

    st.subheader("AI Insight")
    top = g.sort_values("ecl", ascending=False).head(5)
    txt = get_insight(sel_intent, sel_gender, top.to_dict(orient="records"), med)
    st.write(txt)

    st.subheader("Past Reports")
    rlist = list_reports()
    if rlist.empty:
        st.info("No saved reports yet.")
    else:
        rid_sel = st.selectbox("Select report", rlist["rid"].tolist())
        if rid_sel:
            rdf = load_report(rid_sel)
            st.dataframe(rdf)

    st.subheader("CRO Review")
    ins = list_insights()
    if ins.empty:
        st.info("No insights saved yet.")
    else:
        st.dataframe(ins)
        iid_sel = st.selectbox("Select insight to review", ins["iid"].astype(str).tolist())
        dec = st.selectbox("Decision", ["approve", "reject", "defer"])  # CRO decision
        cnote = st.text_input("CRO note")
        if st.button("Update decision", use_container_width=True):
            ok = update_insight(iid_sel, dec, cnote)
            st.success("Updated") if ok else st.error("Update failed")


if __name__ == "__main__":
    main()

