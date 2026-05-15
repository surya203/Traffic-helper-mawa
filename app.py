import folium
import streamlit as st
from streamlit_folium import st_folium

from services.ai_chat import ask_traffic_bot
from services.routing import get_route, save_trip
from services.safety import get_road_rules, get_speed_limit, get_speed_limits

st.set_page_config(page_title="Traffic Advisor Mawa", page_icon="🚦", layout="wide")

st.title("🚦 Traffic Advisor Mawa")
st.caption("Journey planner · AI instructor · Safety advisor")

tab_plan, tab_chat, tab_safety = st.tabs(["Plan Journey", "AI Instructor", "Safety Advisor"])

# --- Plan Journey ---
with tab_plan:
    st.subheader("Plan your trip")
    col1, col2 = st.columns(2)
    with col1:
        from_address = st.text_input("From", placeholder="e.g. Mumbai Central, Mumbai")
    with col2:
        to_address = st.text_input("To", placeholder="e.g. Andheri West, Mumbai")

    if st.button("Get Route", type="primary"):
        if not from_address.strip() or not to_address.strip():
            st.warning("Please enter both From and To addresses.")
        else:
            with st.spinner("Finding route..."):
                try:
                    route = get_route(from_address.strip(), to_address.strip())
                    st.session_state["last_route"] = route
                    st.session_state["last_from"] = from_address.strip()
                    st.session_state["last_to"] = to_address.strip()
                    save_trip(
                        from_address.strip(),
                        to_address.strip(),
                        route["distance_km"],
                        route["duration_min"],
                    )
                except Exception as e:
                    st.error(f"Could not get route: {e}")

    if "last_route" in st.session_state:
        route = st.session_state["last_route"]
        m1, m2 = st.columns(2)
        m1.metric("Distance", f"{route['distance_km']} km")
        m2.metric("Est. duration", f"{route['duration_min']} min")

        if route.get("note"):
            st.info(route["note"])

        center_lat = (route["start"][0] + route["end"][0]) / 2
        center_lon = (route["start"][1] + route["end"][1]) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
        folium.Marker(route["start"], popup="Start", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(route["end"], popup="End", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine(route["coords"], color="blue", weight=4).add_to(m)
        st_folium(m, width=700, height=450)

# --- AI Instructor ---
with tab_chat:
    st.subheader("Ask the traffic instructor")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about traffic, roads, or safety..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Thinking..."):
            reply = ask_traffic_bot(prompt, st.session_state.chat_history[:-1])

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

    if st.session_state.chat_history and st.button("Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

# --- Safety Advisor ---
with tab_safety:
    st.subheader("Road safety tips")

    rules = get_road_rules()
    limits = get_speed_limits()

    topic = st.selectbox(
        "Choose a road rule topic",
        options=list(rules.keys()),
        format_func=lambda k: k.replace("_", " ").title(),
    )
    rule_text = rules.get(topic)
    if rule_text:
        st.success(rule_text)

    st.divider()
    st.subheader("Speed limits")
    area = st.selectbox(
        "Area type",
        options=list(limits.keys()),
        format_func=lambda k: k.replace("_", " ").title(),
    )
    limit_text = get_speed_limit(area)
    if limit_text:
        st.warning(limit_text)
