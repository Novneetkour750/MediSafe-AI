from datetime import datetime

import streamlit as st

import api_client
from components.country_card import render_country_results


def _render_how_it_works() -> None:
    with st.container(key="ms_steps_wrap"):
        st.markdown('<div class="ms-steps-title">How it works?</div>', unsafe_allow_html=True)
        steps = [
            ("1", "Upload Image", "Upload a clear image of your medicine"),
            ("2", "OCR Extraction", "Our AI extracts medicine name and details"),
            ("3", "AI Analysis", "We check global regulations"),
            ("4", "Get Results", "View country-wise status and recommendations"),
        ]
        cols = st.columns(4)
        for c, (num, title, desc) in zip(cols, steps):
            with c:
                st.markdown(
                    f'<div class="ms-step"><div class="ms-step-icon">{num}</div>'
                    f'<div class="ms-step-title">{title}</div><div class="ms-step-desc">{desc}</div></div>',
                    unsafe_allow_html=True,
                )


def _log_history(name: str, method: str, details: list[str]) -> None:
    st.session_state.history.append({
        "name": name, "method": method,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "details": details,
    })


def _get_country_options() -> list[str]:
    try:
        return ["🌍 All Countries"] + api_client.get_countries()
    except api_client.ApiError:
        return ["🌍 All Countries"]


def render_scan() -> None:
    st.markdown('<h1 class="ms-page-title">🔍 Scan Medicine</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ms-page-subtitle">Upload an image of your medicine to get started</p>',
        unsafe_allow_html=True,
    )

    with st.container(key="ms_upload_card"):
        with st.container(key="ms_search_bar_row"):
            toggle_col, input_col = st.columns([0.1, 0.9])

            with toggle_col:
                toggle_icon = "⌨️" if st.session_state.scan_mode == "photo" else "📷"
                toggle_help = (
                    "Switch to typing a medicine name" if st.session_state.scan_mode == "photo"
                    else "Switch to uploading a medicine photo"
                )
                if st.button(toggle_icon, key="scan_mode_toggle", help=toggle_help):
                    st.session_state.scan_mode = "text" if st.session_state.scan_mode == "photo" else "photo"
                    st.session_state.scan_result = None
                    st.rerun()

            uploaded_file, medicine_input = None, None
            with input_col:
                if st.session_state.scan_mode == "photo":
                    uploaded_file = st.file_uploader(
                        "Upload Medicine Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
                    )
                else:
                    medicine_input = st.text_input(
                        "Search Medicine", placeholder="Type a medicine name...", label_visibility="collapsed"
                    )

        country_options = _get_country_options()
        selected_country = st.selectbox("Destination country", country_options, key="scan_destination_country")
        destination_country = None if selected_country == "🌍 All Countries" else selected_country

        analyze = st.button("Analyze Medicine", use_container_width=True, type="primary")

    # Only hit the backend when "Analyze Medicine" is freshly clicked. The
    # outcome is cached in session_state so that later reruns triggered by
    # buttons inside the result cards (Suggest Alternative / Know More)
    # keep showing these results instead of reverting to "How it works".
    if analyze:
        if uploaded_file is not None:
            st.session_state.scan_result = _run_image_scan(uploaded_file, destination_country)
        elif medicine_input:
            st.session_state.scan_result = _run_text_search(medicine_input, destination_country)
        else:
            st.session_state.scan_result = None
        st.session_state.expanded_alternatives = set()

    result = st.session_state.get("scan_result")
    if not result:
        _render_how_it_works()
        return

    if result["kind"] == "image":
        _render_image_result(result)
    elif result["kind"] == "image_error":
        _render_not_detected(result.get("error_detail", ""))
    else:
        _render_text_result(result)


def _run_image_scan(uploaded_file, destination_country: str | None) -> dict:
    image_bytes = uploaded_file.getvalue()
    with st.spinner(" Analyzing medicine... Please wait."):
        try:
            api_result = api_client.scan_image(image_bytes, uploaded_file.name, destination_country)
        except api_client.ApiError as exc:
            return {"kind": "image_error", "error_detail": str(exc)}

    medicine_name = api_result["medicine_name"]
    _log_history(medicine_name, "OCR Upload", [f"Medicine name: {medicine_name}"])
    return {
        "kind": "image",
        "image_bytes": image_bytes,
        "medicine_name": medicine_name,
        "results": api_result["results"],
    }


def _render_image_result(result: dict) -> None:
    st.image(result["image_bytes"], caption="Uploaded Medicine Image")
    st.markdown('<h2 class="ms-section-title"> OCR Analysis Result</h2>', unsafe_allow_html=True)

    medicine_name = result["medicine_name"]
    with st.container(key="ms_result_card_ocr"):
        st.markdown(
            f'<div class="ms-result-header"><span class="ms-result-name">💊 {medicine_name}</span>'
            f'<span class="ms-badge ms-badge-allowed">✅ Detected</span></div>',
            unsafe_allow_html=True,
        )
        render_country_results(result["results"], medicine_name=medicine_name, context_prefix="ocr")

    with st.container(border=True):
        with st.expander(" Detection Details"):
            st.write("• Detected by: Gemini Vision")
            st.write(f"• Medicine name: {medicine_name}")


def _render_not_detected(error_detail: str = "") -> None:
    with st.container(key="ms_result_card_not_detected"):
        st.markdown(
            '<div class="ms-result-header"><span class="ms-result-name">💊 Medicine Not Detected</span>'
            '<span class="ms-badge ms-badge-banned">❌ Not Detected</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="ms-backend-pending">⚠️ We couldn\'t read a medicine name from that photo. '
            'Try a clearer, well-lit, close-up photo, or type the name instead.</div>',
            unsafe_allow_html=True,
        )
        if error_detail:
            st.caption(error_detail)


def _run_text_search(medicine_input: str, destination_country: str | None) -> dict:
    try:
        api_result = api_client.search_medicine(medicine_input, destination_country)
    except api_client.ApiError as exc:
        return {"kind": "text_error", "medicine_input": medicine_input, "error_detail": str(exc)}

    details = [f"Medicine: {medicine_input}", "Search method: Manual Search"]
    if destination_country:
        details.append(f"Destination country: {destination_country}")
    _log_history(medicine_input, "Manual Search", details)

    return {
        "kind": "text",
        "medicine_input": medicine_input,
        "destination_country": destination_country,
        "results": api_result["results"],
    }


def _render_text_result(result: dict) -> None:
    if result["kind"] == "text_error":
        st.markdown('<h2 class="ms-section-title"> Search Result</h2>', unsafe_allow_html=True)
        with st.container(key="ms_result_card_search"):
            st.markdown(
                f'<div class="ms-result-header"><span class="ms-result-name">💊 {result["medicine_input"]}</span>'
                f'<span class="ms-badge ms-badge-required"> Manual Search</span></div>',
                unsafe_allow_html=True,
            )
            st.error(f"Search is unavailable right now ({result['error_detail']}).")
        return

    medicine_input = result["medicine_input"]
    destination_country = result.get("destination_country")

    st.markdown('<h2 class="ms-section-title"> Search Result</h2>', unsafe_allow_html=True)
    with st.container(key="ms_result_card_search"):
        st.markdown(
            f'<div class="ms-result-header"><span class="ms-result-name">💊 {medicine_input}</span>'
            f'<span class="ms-badge ms-badge-required"> Manual Search</span></div>',
            unsafe_allow_html=True,
        )
        render_country_results(result["results"], medicine_name=medicine_input, context_prefix="search")

    with st.container(border=True):
        with st.expander(" Search Details"):
            st.write(f"• Medicine: {medicine_input}")
            st.write("• Search method: Manual Search")
            if destination_country:
                st.write(f"• Destination country: {destination_country}")
