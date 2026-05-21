# dashboard/app.py — Phase 6 Streamlit UI
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="PolicyPulse AI",
    page_icon="🔍",
    layout="wide",
)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def api_get(path: str, **kwargs):
    try:
        return requests.get(f"{API_BASE}{path}", timeout=30, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Cannot reach API at {API_BASE}: {exc}")
        return None


def render_digest(digest: dict | None):
    if not digest or not digest.get("what_changed"):
        st.info("No compliance digest yet (add OPENAI_API_KEY and run digests).")
        return
    st.subheader("Compliance digest")
    st.write("**What changed:**", digest.get("what_changed", ""))
    st.write("**Who is affected:**", digest.get("who_is_affected", ""))
    st.write("**What to do:**", digest.get("what_to_do", ""))
    cols = st.columns(2)
    cols[0].metric("Urgency", digest.get("urgency") or "—")
    cols[1].metric("Key deadline", digest.get("key_deadline") or "—")


# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 PolicyPulse AI")
    st.markdown("*AI policy monitoring*")
    st.caption(f"API: `{API_BASE}`")
    st.divider()

    jurisdiction = st.selectbox("Jurisdiction", ["All", "EU", "US", "UK"])
    risk_level = st.selectbox("Risk level", ["All", "high", "medium", "low"])
    limit = st.slider("Results", 5, 100, 20)

    st.divider()
    st.markdown("**Personal feed** (optional)")
    with st.expander("Login for /user/feed"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            r = requests.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "password": password},
                timeout=15,
            )
            if r.status_code == 200:
                st.session_state["token"] = r.json()["access_token"]
                st.success("Logged in")
            else:
                st.error("Login failed")

# ── Main ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Policy feed", "🔍 Search", "🕐 Recent changes", "📊 Stats"]
)

with tab1:
    st.header("Latest policy documents")
    params = {"limit": limit}
    if jurisdiction != "All":
        params["jurisdiction"] = jurisdiction
    if risk_level != "All":
        params["risk_level"] = risk_level

    resp = api_get("/documents/", params=params)
    if resp and resp.status_code == 200:
        docs = resp.json()
        if not docs:
            st.warning("No documents match these filters.")
        for doc in docs:
            risk = doc.get("risk_level") or "unknown"
            colours = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            label = f"{colours.get(risk, '⚪')} [{doc.get('jurisdiction', '?')}] {doc['title'][:90]}"
            with st.expander(label):
                col1, col2 = st.columns([2, 1])
                with col1:
                    if doc.get("summary"):
                        st.write(doc["summary"])
                    if doc.get("change_summary"):
                        st.warning(f"Recent change (~{doc.get('change_percent', '?')}%): {doc['change_summary'][:300]}")
                    st.markdown(f"[Open source document]({doc['url']})")
                    render_digest(doc.get("digest"))
                with col2:
                    st.metric("Risk", risk)
                    if doc.get("doc_type"):
                        st.caption(f"Type: {doc['doc_type']}")
                    if st.button("Load full detail", key=f"detail_{doc['id']}"):
                        detail = api_get(f"/documents/{doc['id']}")
                        if detail and detail.status_code == 200:
                            st.json(detail.json())
    elif resp:
        st.error(f"Could not load documents ({resp.status_code}). Is the API running?")

    if st.session_state.get("token"):
        st.divider()
        st.subheader("Your personalised feed")
        feed = requests.get(
            f"{API_BASE}/user/feed",
            params={"limit": limit},
            headers={"Authorization": f"Bearer {st.session_state['token']}"},
            timeout=30,
        )
        if feed.status_code == 200:
            for item in feed.json():
                st.write(f"**{item['score']:.0%}** — [{item['jurisdiction']}] {item['title']}")
        else:
            st.caption("Complete POST /user/profile in Swagger if feed is empty.")

with tab2:
    st.header("Semantic search")
    query = st.text_input("Search", placeholder="e.g. facial recognition EU regulation")
    if query:
        resp = api_get("/search/", params={"q": query, "limit": 10})
        if resp and resp.status_code == 200:
            results = resp.json()
            if not results:
                st.info("No results — embed more documents (`python3 -m ml_pipeline.embedder`).")
            st.write(f"Found **{len(results)}** results")
            for r in results:
                st.write(
                    f"**{r['title']}** — {r.get('jurisdiction', '?')} — "
                    f"{round(r['similarity'] * 100)}% match"
                )
        elif resp and resp.status_code == 503:
            st.warning(resp.json().get("detail", "Search unavailable"))

with tab3:
    st.header("Recent changes")
    st.caption("Documents flagged as updated or materially changed")
    resp = api_get("/documents/", params={"limit": 100})
    if resp and resp.status_code == 200:
        docs = resp.json()
        changed = [
            d
            for d in docs
            if d.get("is_major_change") or d.get("change_percent") or d.get("change_summary")
        ]
        if not changed:
            st.info("No change flags in the latest 100 documents.")
        for doc in sorted(
            changed,
            key=lambda x: x.get("change_percent") or 0,
            reverse=True,
        ):
            with st.container(border=True):
                st.markdown(f"### {doc['title']}")
                st.caption(
                    f"{doc.get('jurisdiction', '?')} · "
                    f"Change: {doc.get('change_percent', '—')}% · "
                    f"Major: {doc.get('is_major_change', False)}"
                )
                if doc.get("change_summary"):
                    st.write(doc["change_summary"])
                render_digest(doc.get("digest"))

with tab4:
    st.header("Database stats")
    resp = api_get("/stats/")
    if resp and resp.status_code == 200:
        data = resp.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total documents", data.get("total", 0))
        c2.metric("Jurisdictions", len(data.get("by_jurisdiction", {})))
        c3.metric("High risk", data.get("high_risk", 0))

        by_j = data.get("by_jurisdiction", {})
        if by_j:
            df = pd.DataFrame(
                [{"jurisdiction": k, "count": v} for k, v in by_j.items()]
            )
            fig = px.pie(df, names="jurisdiction", values="count", title="By jurisdiction")
            st.plotly_chart(fig, use_container_width=True)

        by_src = data.get("by_source", {})
        if by_src:
            st.subheader("By source")
            st.dataframe(
                pd.DataFrame(
                    [{"source": k, "documents": v} for k, v in by_src.items()]
                ),
                use_container_width=True,
                hide_index=True,
            )
    elif resp:
        st.error("Stats endpoint unavailable")
