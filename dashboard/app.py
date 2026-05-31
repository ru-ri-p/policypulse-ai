# dashboard/app.py — Phase 6 Streamlit UI
import os
from datetime import datetime

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

UPDATE_LABELS = {
    "new": ("🆕 New", "First time ingested — no prior version on file"),
    "updated": ("📝 Updated", "Source text changed; prior version archived"),
    "major_update": ("⚠️ Major revision", "Material change (>20% text delta)"),
}


def api_get(path: str, **kwargs):
    try:
        return requests.get(f"{API_BASE}{path}", timeout=30, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Cannot reach API at {API_BASE}: {exc}")
        return None


def format_dt(iso_str: str | None, date_only: bool = False) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if date_only:
            return dt.strftime("%d %b %Y")
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return iso_str[:10] if date_only else iso_str[:16]


def policy_date_label(doc: dict) -> str:
    """Publication date shown to users (not ingest/scrape time)."""
    if doc.get("published_at"):
        return format_dt(doc["published_at"], date_only=True)
    jur = doc.get("jurisdiction") or ""
    if jur in ("UAE", "SA", "QA", "BH"):
        return "Not listed on source"
    return "Not listed on source"


def render_update_badge(doc: dict):
    status = doc.get("update_status") or "new"
    label, hint = UPDATE_LABELS.get(status, ("—", ""))
    st.markdown(f"**Status:** {label}")
    st.caption(hint)
    if doc.get("version_count", 0) > 0:
        st.caption(f"Archived versions: **{doc['version_count']}**")


def render_playbook_impacts(impacts: dict | None, exposure_pack: str | None = None):
    if not impacts:
        st.caption(
            "No playbook impacts yet — zones are rule-tagged (no OpenAI). "
            "Run: `python3 -m ingestion.retag_documents`"
        )
        return
    if exposure_pack:
        resp = api_get(f"/playbooks/exposure-packs/{exposure_pack}")
        if resp and resp.status_code == 200:
            allowed = set(resp.json().get("default_playbooks", []))
            impacts = {k: v for k, v in impacts.items() if k in allowed}
    if not impacts:
        st.caption("No impacts for selected exposure pack.")
        return
    st.subheader("Playbook impact")
    for pid, data in sorted(
        impacts.items(),
        key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x[1].get("level"), 3),
    ):
        level = data.get("level", "low")
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
        st.write(f"{icon} **{data.get('name', pid)}** ({level})")
        if data.get("summary"):
            st.caption(data["summary"][:200])


def render_zone_guide(selected_zone: str):
    resp = api_get("/playbooks/")
    if not resp or resp.status_code != 200:
        return
    playbooks = resp.json()
    if selected_zone != "All":
        playbooks = [p for p in playbooks if selected_zone in p.get("zones", [])]
    if not playbooks:
        st.caption(f"No playbooks mapped to zone **{selected_zone}**.")
        return
    for pb in playbooks:
        st.markdown(f"**{pb['name']}**")
        if pb.get("impact_summary"):
            st.caption(pb["impact_summary"])
        st.caption(
            f"Sectors: {', '.join(pb.get('sectors', []))} · "
            f"Jurisdictions: {', '.join(pb.get('jurisdictions', []))}"
        )


def render_digest(digest: dict | None):
    if not digest or not digest.get("what_changed"):
        st.info(
            "No AI compliance digest yet. Digests need **OPENAI_API_KEY** and "
            "`python3 digests/run_digests.py` (or Celery). "
            "Zones, dates, and change flags work without OpenAI."
        )
        return
    st.subheader("Compliance digest")
    st.write("**What changed:**", digest.get("what_changed", ""))
    st.write("**Who is affected:**", digest.get("who_is_affected", ""))
    st.write("**What to do:**", digest.get("what_to_do", ""))
    cols = st.columns(2)
    cols[0].metric("Urgency", digest.get("urgency") or "—")
    cols[1].metric("Key deadline", digest.get("key_deadline") or "—")


def build_feed_params(limit, jurisdiction, region, risk_level, zone, keyword):
    params = {"limit": limit}
    if jurisdiction != "All":
        params["jurisdiction"] = jurisdiction
    elif region != "All":
        params["region"] = region
    if risk_level != "All":
        params["risk_level"] = risk_level
    if zone != "All":
        params["zone"] = zone
    if keyword and keyword.strip():
        params["q"] = keyword.strip()
    return params


# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 PolicyPulse AI")
    st.markdown("*AI policy monitoring — GCC & global*")
    st.caption(f"API: `{API_BASE}`")
    st.info(
        "Sidebar filters apply to the **Policy feed** tab. "
        "Semantic **Search** uses its own query box."
    )
    st.divider()

    region = st.selectbox(
        "Region",
        ["All", "MENA", "EU", "US", "UK"],
        index=0,
        help="MENA pages often omit publication dates on the site; US Federal Register includes them.",
    )
    jurisdiction = st.selectbox(
        "Jurisdiction",
        ["All", "UAE", "SA", "EU", "US", "UK", "QA", "BH", "OECD"],
    )
    zone = st.selectbox(
        "Zone",
        ["All", "DIFC", "ADGM", "MAINLAND", "DMCC"],
        help="UAE regulatory layer. Requires zone tags on documents (run retag_documents).",
    )
    exposure_pack = st.selectbox(
        "Exposure pack",
        ["dubai_hq", "mena_only", "eu_exposure_only", "none"],
        index=0,
        help="dubai_hq = GCC + EU + US for Dubai HQ companies",
    )
    risk_level = st.selectbox("Risk level", ["All", "high", "medium", "low"])
    keyword = st.text_input(
        "Keyword in title/summary",
        placeholder="e.g. DIFC, AI Act, PDPL",
        help="Filters the policy feed (not semantic search).",
    )
    limit = st.slider("Results", 5, 100, 20)

    with st.expander("What affects each zone?"):
        render_zone_guide(zone)

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
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📋 Policy feed", "🔍 Search", "🕐 Recent changes", "📊 Stats", "📄 Weekly brief"]
)

with tab1:
    st.header("Latest policy documents")
    if region == "MENA":
        st.info(
            "Many GCC source pages (Digital Dubai, DIFC marketing pages, etc.) do not "
            "publish a formal **policy date** on the page. US Federal Register items include "
            "official publication dates. Try **Region → All** or **US** to see dated policies."
        )
    params = build_feed_params(limit, jurisdiction, region, risk_level, zone, keyword)

    resp = api_get("/documents/", params=params)
    if resp and resp.status_code == 200:
        docs = resp.json()
        if not docs:
            st.warning("No documents match these filters.")
            if zone != "All":
                st.markdown(
                    f"**Zone `{zone}`** needs documents tagged with that zone. "
                    "Most US/EU items have no UAE zone. Try **Region: MENA** or **All**, "
                    "or run:\n\n`python3 -m ingestion.retag_documents`"
                )
        for doc in docs:
            risk = doc.get("risk_level") or "unknown"
            colours = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            status = doc.get("update_status", "new")
            status_icon = {"new": "🆕", "updated": "📝", "major_update": "⚠️"}.get(
                status, ""
            )
            pub_label = policy_date_label(doc)
            label = (
                f"{status_icon}{colours.get(risk, '⚪')} "
                f"[{doc.get('jurisdiction', '?')}] {doc['title'][:80]} · Pub. {pub_label}"
            )
            with st.expander(label):
                col1, col2 = st.columns([2, 1])
                with col1:
                    if doc.get("summary"):
                        st.write(doc["summary"])
                    if doc.get("change_summary"):
                        st.warning(
                            f"Change detail (~{doc.get('change_percent', '?')}%): "
                            f"{doc['change_summary'][:400]}"
                        )
                    zones = ", ".join(doc.get("zones") or []) or "—"
                    sectors = ", ".join(doc.get("sectors") or []) or "—"
                    st.caption(f"Zones: {zones} · Sectors: {sectors}")
                    st.markdown(f"[Open source document]({doc['url']})")
                    pack = exposure_pack if exposure_pack != "none" else None
                    render_playbook_impacts(doc.get("playbook_impacts"), pack)
                    render_digest(doc.get("digest"))
                with col2:
                    st.metric("Risk", risk)
                    render_update_badge(doc)
                    st.metric("Published", pub_label)
                    st.caption(
                        f"**Ingested into PolicyPulse:** "
                        f"{format_dt(doc.get('first_scraped_at'), date_only=True)}"
                    )
                    if doc.get("scraped_at") and doc.get("first_scraped_at") != doc.get("scraped_at"):
                        st.caption(
                            f"**Last checked:** {format_dt(doc.get('scraped_at'), date_only=True)}"
                        )
                    if doc.get("doc_type"):
                        st.caption(f"Type: {doc['doc_type']}")
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
    st.caption(
        "Uses embeddings (sentence-transformers), not OpenAI. "
        "Sidebar region/zone filters do not apply here yet."
    )
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
    st.caption("Updated or materially revised documents (from diff engine, not OpenAI)")
    resp = api_get("/documents/", params={"limit": 100})
    if resp and resp.status_code == 200:
        docs = resp.json()
        changed = [
            d
            for d in docs
            if d.get("update_status") in ("updated", "major_update")
            or d.get("is_major_change")
            or d.get("change_summary")
        ]
        if not changed:
            st.info("No updates in the latest 100 documents.")
        for doc in sorted(
            changed,
            key=lambda x: x.get("change_percent") or 0,
            reverse=True,
        ):
            with st.container(border=True):
                st.markdown(f"### {doc['title']}")
                render_update_badge(doc)
                st.caption(
                    f"{doc.get('jurisdiction', '?')} · "
                    f"Published {policy_date_label(doc)} · "
                    f"Ingested {format_dt(doc.get('first_scraped_at'), date_only=True)} · "
                    f"Change: {doc.get('change_percent', '—')}%"
                )
                if doc.get("change_summary"):
                    st.write(doc["change_summary"])
                render_digest(doc.get("digest"))

with tab4:
    st.header("Database stats")
    resp = api_get("/stats/")
    if resp and resp.status_code == 200:
        data = resp.json()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total documents", data.get("total", 0))
        c2.metric("Jurisdictions", len(data.get("by_jurisdiction", {})))
        c3.metric("High risk", data.get("high_risk", 0))
        mena_count = data.get("by_region", {}).get("MENA", 0)
        c4.metric("MENA documents", mena_count)

        col_left, col_right = st.columns(2)

        by_region = data.get("by_region", {})
        if by_region:
            with col_left:
                df_r = pd.DataFrame(
                    [{"region": k, "count": v} for k, v in by_region.items()]
                )
                fig_r = px.pie(df_r, names="region", values="count", title="By region")
                st.plotly_chart(fig_r, use_container_width=True)

        by_j = data.get("by_jurisdiction", {})
        if by_j:
            with col_right:
                df = pd.DataFrame(
                    [{"jurisdiction": k, "count": v} for k, v in by_j.items()]
                )
                fig = px.bar(df, x="jurisdiction", y="count", title="By jurisdiction")
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

with tab5:
    st.header("Weekly compliance brief (PDF)")
    st.markdown(
        "Generate a PDF for investors or clients using the **exposure pack** in the sidebar."
    )
    st.code(
        "./scripts/generate_weekly_brief.sh --exposure-pack dubai_hq --days 7",
        language="bash",
    )
    pack_id = exposure_pack if exposure_pack != "none" else "dubai_hq"
    pack_resp = api_get(f"/playbooks/exposure-packs/{pack_id}")
    if pack_resp and pack_resp.status_code == 200:
        pack = pack_resp.json()
        st.write(f"**{pack['name']}**")
        st.caption(pack.get("description", ""))
        st.write("Jurisdictions monitored:", ", ".join(pack.get("jurisdictions", [])))
        st.write("Default playbooks:", ", ".join(pack.get("default_playbooks", [])[:6]), "…")
