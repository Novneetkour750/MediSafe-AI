import re

import streamlit as st

import api_client
from state import go_to


def _status_style(status: str) -> tuple[str, str]:
    s = (status or "").lower()
    if "allow" in s:
        return "ms-badge-allowed", "✅"
    if "restrict" in s:
        return "ms-badge-restricted", "⚠️"
    if "prescription" in s:
        return "ms-badge-required", "📋"
    if "ban" in s:
        return "ms-badge-banned", "⛔"
    return "ms-badge-neutral", "ℹ️"


def render_alternative_panel(alternatives: list[dict], country: str, source: str) -> None:
    html = '<div class="ms-alt-panel">'
    if alternatives:
        title = (
            "💡 Alternative suggested in our records"
            if source == "database"
            else f"💡 Other medicines allowed in {country}"
        )
        html += f'<div class="ms-alt-title">{title}</div><div class="ms-alt-chip-row">'
        for alt in alternatives:
            label = alt.get("name", "")
            if not label:
                continue
            if alt.get("generic_name"):
                label += f" ({alt['generic_name']})"
            html += f'<span class="ms-alt-chip">✅ {label}</span>'
        html += "</div>"
    else:
        html += (
            '<div class="ms-alt-title">💡 No specific alternative on file</div>'
            '<div class="ms-country-detail">We couldn\'t find a similar allowed medicine in our '
            'data for this country. Try asking the AI Assistant or a local pharmacist.</div>'
        )
    html += (
        '<div class="ms-alt-disclaimer">⚠️ Suggested from our regulation database only — '
        'always verify with a licensed doctor or pharmacist before using any alternative medicine.</div>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_country_result_card(entry: dict, medicine_name: str = "", card_key: str = "card") -> None:
    flag, country, status = entry.get("flag", ""), entry.get("country"), entry.get("status")
    reason, travel_advice, alternative = entry.get("reason"), entry.get("travel_advice"), entry.get("alternative")
    confidence = entry.get("confidence")

    html = '<div class="ms-country-card"><div class="ms-country-card-header">'
    if country:
        html += f'<span class="ms-country-name">{flag} {country}</span>'
    if status:
        cls, icon = _status_style(status)
        html += f'<span class="ms-badge {cls}">{icon} {status}</span>'
    html += "</div>"
    if reason:
        html += f'<div class="ms-country-detail"><strong>Reason:</strong> {reason}</div>'
    if travel_advice:
        html += f'<div class="ms-country-detail"><strong>Travel advice:</strong> {travel_advice}</div>'
    if confidence is not None:
        pct = max(0, min(100, int(confidence)))
        html += (
            f'<div class="ms-confidence-row">'
            f'<div class="ms-confidence-track"><div class="ms-confidence-fill" style="width:{pct}%;"></div></div>'
            f'<span class="ms-confidence-label">{pct}% confidence</span></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="ms-card-actions">', unsafe_allow_html=True)
    action_cols = st.columns(2)

    with action_cols[0]:
        if st.button("💊 Suggest Alternative", key=f"alt_btn_{card_key}", use_container_width=True):
            if card_key in st.session_state.expanded_alternatives:
                st.session_state.expanded_alternatives.discard(card_key)
            else:
                st.session_state.expanded_alternatives.add(card_key)
    know_more_col = action_cols[1]

    with know_more_col:
        if st.button("🤖 Know More", key=f"km_btn_{card_key}", use_container_width=True):
            st.session_state.chat_context = {
                "medicine_name": medicine_name, "country": country, "status": status,
                "reason": reason, "travel_advice": travel_advice, "alternative": alternative,
            }
            st.session_state.chat_autoquery = (
                f"Tell me more about {medicine_name or 'this medicine'}'s regulatory status "
                f"in {country or 'this country'} and what I should know before traveling."
            )
            go_to("AI Chat")

    st.markdown("</div>", unsafe_allow_html=True)

    if card_key in st.session_state.expanded_alternatives:
        try:
            result = api_client.get_alternatives(entry, medicine_name)
            render_alternative_panel(result["alternatives"], country or "your destination", result["source"])
        except api_client.ApiError as exc:
            st.warning(f"Couldn't load alternatives right now ({exc}).")


def render_country_results(country_results: list[dict], medicine_name: str = "", context_prefix: str = "result") -> None:
    if not country_results:
        st.markdown(
            '<div class="ms-backend-pending">🔍 No matching regulation entries were found for this medicine.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="ms-country-grid">', unsafe_allow_html=True)
    for i, entry in enumerate(country_results):
        country_slug = re.sub(r"\W+", "_", (entry.get("country") or "na")).strip("_")
        render_country_result_card(entry, medicine_name=medicine_name, card_key=f"{context_prefix}_{i}_{country_slug}")
    st.markdown("</div>", unsafe_allow_html=True)
