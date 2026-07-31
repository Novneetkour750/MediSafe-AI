import streamlit as st
import streamlit.components.v1 as components

import api_client
from config import BOT_AVATAR

AI_UNAVAILABLE_MESSAGE = "MediSafe AI couldn't process that question right now. Please try again in a moment."

_LAST_MESSAGE_ANCHOR_ID = "ms-last-message-anchor"
_CHAT_BOX_HEIGHT = 460
_MIN_MESSAGES_FOR_SCROLL_BOX = 5


def _apply_scroll_behavior(scroll_to_last_message: bool) -> None:
    
    target = "true" if scroll_to_last_message else "false"
    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;
            var win = window.parent;
            var scrollToLastMessage = {target};
            var anchorId = "{_LAST_MESSAGE_ANCHOR_ID}";
            var expectedHeight = {_CHAT_BOX_HEIGHT};
            var tolerance = 60;

            function findChatBox(el) {{
                var node = el ? el.parentElement : null;
                while (node && node !== doc.body) {{
                    var style = win.getComputedStyle(node);
                    var isScrollable = (style.overflowY === "auto" || style.overflowY === "scroll");
                    if (isScrollable && Math.abs(node.clientHeight - expectedHeight) <= tolerance) {{
                        return node;
                    }}
                    node = node.parentElement;
                }}
                return null;
            }}

            function applyTarget() {{
                var anchor = doc.getElementById(anchorId);
                var box = findChatBox(anchor);
                if (!box) {{ return; }}
                box.scrollTop = scrollToLastMessage ? box.scrollHeight : 0;
            }}

            
            applyTarget();
            setTimeout(applyTarget, 100);
            setTimeout(applyTarget, 400);
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

    chat_box_kwargs = {"key": "ms_chat_card"}
    if len(st.session_state.chat_messages) >= _MIN_MESSAGES_FOR_SCROLL_BOX:
        chat_box_kwargs["height"] = _CHAT_BOX_HEIGHT

    with st.container(**chat_box_kwargs):
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

    if not user_query:
        
        has_conversation = len(st.session_state.chat_messages) > 1
        _apply_scroll_behavior(scroll_to_last_message=has_conversation)
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
