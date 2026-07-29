import streamlit as st
import streamlit.components.v1 as components

import api_client
from config import BOT_AVATAR

AI_UNAVAILABLE_MESSAGE = "MediSafe AI couldn't process that question right now. Please try again in a moment."

_LAST_MESSAGE_ANCHOR_ID = "ms-last-message-anchor"


def _apply_scroll_behavior(scroll_to_last_message: bool) -> None:
    """Streamlit's chat_input auto-focuses on every rerun, which drags the
    whole page down to the very bottom. Streamlit does this at a timing we
    don't control, so instead of fixing the scroll position once, we keep
    re-asserting the target position for about a second — that way, whenever
    Streamlit's own scroll/focus fires, ours wins right after it.

    - first visit to the page: don't scroll at all, stay at the top.
    - later reruns: scroll only far enough to reveal the last message,
      not all the way to the bottom of the page.
    """
    target = "true" if scroll_to_last_message else "false"
    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;
            var scrollToLastMessage = {target};
            var anchorId = "{_LAST_MESSAGE_ANCHOR_ID}";

            function getScrollEl() {{
                return doc.scrollingElement || doc.documentElement || doc.body;
            }}

            function blurChatInputIfFocused() {{
                var ta = doc.querySelector('[data-testid="stChatInput"] textarea');
                if (ta && doc.activeElement === ta) {{ ta.blur(); }}
            }}

            function applyTarget() {{
                blurChatInputIfFocused();
                if (scrollToLastMessage) {{
                    var el = doc.getElementById(anchorId);
                    if (el) {{ el.scrollIntoView({{behavior: "auto", block: "end"}}); }}
                }} else {{
                    var scrollEl = getScrollEl();
                    if (scrollEl) {{ scrollEl.scrollTop = 0; }}
                    var container = doc.querySelector('[data-testid="stAppViewContainer"]');
                    if (container) {{ container.scrollTop = 0; }}
                    window.parent.scrollTo(0, 0);
                }}
            }}

            // Keep re-asserting for ~1s to win the race against Streamlit's
            // own autofocus/scroll, whenever that happens to fire.
            [0, 30, 60, 100, 150, 250, 400, 600, 900].forEach(function(ms) {{
                setTimeout(applyTarget, ms);
            }});
        }})();
        </script>
        """,
        height=0,
    )


def render_chat() -> None:
    st.markdown('<h1 class="ms-page-title">💬 AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ms-page-subtitle">Ask me anything about medicines and travel regulations</p>',
        unsafe_allow_html=True,
    )

    context = st.session_state.get("chat_context")
    if context:
        banner_bits = [
            f"💊 {context.get('medicine_name')}" if context.get("medicine_name") else None,
            f"in {context.get('country')}" if context.get("country") else None,
            f"— {context.get('status')}" if context.get("status") else None,
        ]
        banner_text = " ".join(b for b in banner_bits if b)
        st.markdown(
            f'<div class="ms-chat-context-banner">🔎 <strong>Know More:</strong> {banner_text}</div>',
            unsafe_allow_html=True,
        )
        if st.button("✖️ Exit Know More mode", key="exit_know_more"):
            st.session_state.chat_context = None
            st.rerun()

    with st.container(key="ms_chat_card"):
        for msg in st.session_state.chat_messages:
            if msg["role"] == "system":
                st.markdown(f'<div class="ms-chat-system-notice">🔒 {msg["text"]}</div>', unsafe_allow_html=True)
            else:
                if msg["role"] == "assistant":
                    avatar = str(BOT_AVATAR) if BOT_AVATAR.exists() else "🤖"
                else:
                    avatar = "🧑"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["text"])
        st.markdown(f'<div id="{_LAST_MESSAGE_ANCHOR_ID}"></div>', unsafe_allow_html=True)

    suggestions = [
        "Is Paracetamol allowed in USA?",
        "Can I carry medicine without prescription?",
        "What is considered a personal quantity?",
    ]
    clicked_suggestion = None
    with st.container(key="ms_suggested_q"):
        s_cols = st.columns(len(suggestions))
        for c, s in zip(s_cols, suggestions):
            with c:
                if st.button(s, key=f"sugg_{s}", use_container_width=True):
                    clicked_suggestion = s

    typed = st.chat_input("Type your question...")
    autoquery = st.session_state.pop("chat_autoquery", None)
    user_query = autoquery or clicked_suggestion or typed

    _apply_scroll_behavior(scroll_to_last_message=st.session_state.chat_visited)
    st.session_state.chat_visited = True

    if not user_query:
        return

    st.session_state.chat_messages.append({"role": "user", "text": user_query})

    with st.spinner("MediSafe AI is typing..."):
        try:
            if st.session_state.get("chat_context"):
                reply = api_client.chat_followup(user_query, st.session_state.chat_context)
            else:
                reply = api_client.chat(user_query)
            st.session_state.chat_messages.append({"role": "assistant", "text": reply})
        except api_client.ApiError as exc:
            st.session_state.chat_messages.append({
                "role": "system", "text": f"{AI_UNAVAILABLE_MESSAGE} (Error: {exc})"
            })

    st.rerun()
