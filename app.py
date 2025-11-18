import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from data import load_clean
from pd_model import build_pd
from ecl import add_ecl, aggregate
from ai import get_insight
from config import set_api_key, get_api_key
from auth import ensure_default_users, verify_login, create_user, list_users, update_segments
from storage import (
    save_report,
    list_reports,
    load_report,
    save_insight,
    list_insights,
    update_insight,
    list_reports_for_user,
)

st.set_page_config(page_title="ECL Dashboard", layout="centered")
st.set_option("client.showErrorDetails", False)


def _format_label(val: str) -> str:
    s = str(val).strip()
    norm = s.lower().replace("_", "").replace(" ", "")
    special = {
        "debtconsolidation": "Debt Consolidation",
        "homeimprovement": "Home Improvement",
    }
    if norm in special:
        return special[norm]
    s = s.replace("_", " ")
    return s.title()


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
    # Seed demo users only if explicitly enabled via env var
    seed = str(os.environ.get("SEED_DEFAULT_USERS", "")).strip().lower()
    if seed in {"1", "true", "yes"}:
        ensure_default_users()

    # Authentication gate
    if "user" not in st.session_state:
        tab1, tab2 = st.tabs(["Login", "Create account"])
        with tab1:
            st.subheader("Login")
            u = st.text_input("User ID", key="login_user")
            p = st.text_input("Password", type="password", key="login_pass")
            role_disp = st.selectbox("Role (Login)", ["Analyst", "CRO"], key="login_role_select")  # enforce role on login
            role_val = "analyst" if role_disp == "Analyst" else "cro"
            if st.button("Login", use_container_width=True):
                user = verify_login(u, p, role_val)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        with tab2:
            st.subheader("Create Account")
            u2 = st.text_input("New User ID", key="create_user")
            p2 = st.text_input("New Password", type="password", key="create_pass")
            role2_disp = st.selectbox("Role (Create)", ["Analyst", "CRO"], key="create_role_select")  # clean labels
            role2 = "analyst" if role2_disp == "Analyst" else "cro"
            if st.button("Create", use_container_width=True):
                ok = create_user(u2, p2, role2)
                if ok:
                    new_user = verify_login(u2, p2, role2)
                    if new_user:
                        st.session_state["user"] = new_user
                        st.success("Account created. Logging you in...")
                        st.rerun()
                    else:
                        st.success("Account created. Please login.")
                else:
                    st.error("Username exists or invalid input.")
        return

    user = st.session_state["user"]
    st.sidebar.markdown(f"**Logged in:** {user['username']} ({str(user['role']).upper()})")
    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.rerun()

    df = run_model_and_metrics()

    intents = sorted(df["loan_intent"].unique().tolist())
    genders = sorted(df["person_gender"].unique().tolist())

    st.sidebar.header("Filters")
    # Role-based allowed segments (simple: '*' => all)
    allowed = user.get("segments", {"*": ["*"]})
    intents_allowed = intents if "*" in allowed or allowed.get("loan_intent", ["*"]) == ["*"] else [v for v in intents if v in allowed.get("loan_intent", [])]
    genders_allowed = genders if "*" in allowed or allowed.get("person_gender", ["*"]) == ["*"] else [v for v in genders if v in allowed.get("person_gender", [])]

    # Empty by default; users decide what to add
    sel_intent = st.sidebar.multiselect("Loan Intent", intents_allowed, default=[], format_func=_format_label)
    sel_gender = st.sidebar.multiselect("Gender", genders_allowed, default=[], format_func=_format_label)

    if not sel_intent or not sel_gender:
        st.info("Select loan intent and gender to see ECL results.")
        return
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
            rid = save_report(g, med, saved_by=user["username"])
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
    # Settings for API key (only show if no key stored)
    cur = get_api_key()
    if not cur:
        with st.expander("Settings: AI API"):
            with st.form("api_key_form"):
                new_key = st.text_input("Gemini API key", value="", type="password")
                submitted = st.form_submit_button("Save API key")
                if submitted:
                    ok = set_api_key(new_key)
                    if ok:
                        st.success("Saved")
                        st.rerun()
                    else:
                        st.error("Save failed")

    top = g.sort_values("ecl", ascending=False).head(5)
    try:
        txt = get_insight(sel_intent, sel_gender, top.to_dict(orient="records"), med)
        st.markdown(txt if isinstance(txt, str) else str(txt))
    except Exception:
        st.info("Insight temporarily unavailable. Please try again later.")

    st.subheader("Past Reports")
    rlist = list_reports() if user["role"] == "cro" else list_reports_for_user(user["username"])  
    if rlist.empty:
        st.info("No saved reports yet.")
    else:
        rid_sel = st.selectbox("Select report", rlist["rid"].tolist())
        if rid_sel:
            rdf = load_report(rid_sel)
            st.dataframe(rdf)

    if user["role"] == "cro":
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

        st.subheader("Manage Analyst Access")
        users = list_users()
        analysts = users[users["role"] == "analyst"]["username"].tolist() if not users.empty else []
        if not analysts:
            st.info("No analysts found.")
        else:
            target = st.selectbox("Select analyst", analysts)
            intents = sorted(df["loan_intent"].unique().tolist())
            genders = sorted(df["person_gender"].unique().tolist())
            allow_intents = st.multiselect("Allow loan intents", intents, default=intents)
            allow_genders = st.multiselect("Allow genders", genders, default=genders)
            if st.button("Save access", use_container_width=True):
                segs = {"loan_intent": allow_intents, "person_gender": allow_genders}
                ok = update_segments(target, segs)
                st.success("Access updated") if ok else st.error("Update failed")


if __name__ == "__main__":
    main()

