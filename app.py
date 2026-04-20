"""
자동개발루프 시스템 - Streamlit Cloud
API 키는 Cloud Secrets에서 자동 읽기
"""

import streamlit as st
import os
import json
import time
import threading
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

# ─── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="자동개발루프",
    page_icon="⚡",
    layout="centered",
)

# ─── 스타일 ─────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: #0a0e14; }
    .block-container { padding-top: 2rem; max-width: 800px; }

    div[data-testid="stMetric"] {
        background: #111820;
        border: 1px solid #2a3444;
        border-radius: 12px;
        padding: 1rem;
    }

    div[data-testid="stMetric"] label {
        color: #6b7a8d !important;
        font-size: 0.75rem !important;
    }

    .log-box {
        background: #111820;
        border: 1px solid #2a3444;
        border-radius: 12px;
        padding: 1rem;
        max-height: 400px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 0.8rem;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)


# ─── 모델 목록 ───────────────────────────────────────────────
MODELS = {
    # OpenAI
    "GPT-4o":            {"provider": "openai",    "model": "gpt-4o"},
    "GPT-4o mini":       {"provider": "openai",    "model": "gpt-4o-mini"},
    "GPT-4 Turbo":       {"provider": "openai",    "model": "gpt-4-turbo"},
    "o3-mini":           {"provider": "openaio1":                {"provider": "openai",    "model": "o1"},
    # Anthropic (Claude)
    "Claude 3.5 Sonnet": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
    "Claude 3.5 Haiku":  {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
    "Claude 3 Opus":     {"provider": "anthropic", "model": "claude-3-opus-20240229"},
}


# ─── API 키 로드 (Secrets 우선) ─────────────────────────────
def get_api_keys():
    openai_key = ""
    anthropic_key = ""

    try:
        openai_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        openai_key = os.environ.get("OPENAI_API_KEY", "")

    try:
        anthropic_key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    return openai_key, anthropic_key


# ─── 세션 초기화 ─────────────────────────────────────────────
def init():
    for k, v in {
        "running": False,
        "stage": "대기 중",
        "cycles": 0,
        "logs": [],
        "code_input": "",
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── 로그 ────────────────────────────────────────────────────
def log(msg, level="info"):
    st.session_state.logs.append({
        "t": datetime.now().strftime("%H:%M:%S"),
        "msg": msg,
        "level": level,
    })
    if len(st.session_state.logs) > 200:
        st.session_state.logs = st.session_state.logs[-200:]


# ─── AI 호출 ─────────────────────────────────────────────────
def call_openai(prompt, api_key, model):
    if not OpenAI:
        return False, "openai 패키지 미설치"
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 전문 개발자입니다. 코드를 분석하고 개선합니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return True, resp.choices[0].message.content
    except Exception as e:
        return False, str(e)


def call_anthropic(prompt, api_key, model):
    if not anthropic:
        return False, "anthropic 패키지 미설치"
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=4000,
            system="당신은 전문 개발자입니다. 코드를 분석하고 개선합니다.",
            messages=[{"role": "user", "content": prompt}],
        )
        return True, resp.content[0].text
    except Exception as e:
        return False, str(e)


def call_ai(prompt, model_name):
    config = MODELS[model_name]
    openai_key, anthropic_key = get_api_keys()

    if config["provider"] == "openai":
        if not openai_key:
            return False, "OpenAI API 키가 Secrets에 설정되지 않았습니다"
        return call_openai(prompt, openai_key, config["model"])

    elif config["provider"] == "anthropic":
        if not anthropic_key:
            return False, "Anthropic API 키가 Secrets에 설정되지 않았습니다"
        return call_anthropic(prompt, anthropic_key, config["model"])

    return False, "알 수 없는 모델"


# ─── 루프 ────────────────────────────────────────────────────
def run_cycle(code, model_name):
    stages = [
        ("하드닝 (개선)", "다음 코드를 분석하고 개선하세요. 보안, 성능, 가독성을 향상시키세요.\n\n코드:\n"),
        ("디버그", "다음 코드의 버그를 찾아 수정하세요.\n\n코드:\n"),
    ]

    current_code = code

    for stage_name, prompt_prefix in stages:
        if",    "model": "o3-mini"},
    " not st.session_state"═══ 사이클 {st.session_state.cycles} ═══", "info")

        result = run_cycle(current_code, model_name)
        if result is None:
            break
        current_code = result
        log(f"═══ 사이클 {st.session_state.cycles} 완료 ═══", "info")
        time.sleep(2)

    st.session_state.running = False
    st.session_state.stage = "대기 중"
    st.session_state.final_code = current_code
    log("루프 종료", "warn")


# ─── 토글 ────────────────────────────────────────────────────
def on_toggle():
    if st.session_state.toggle:
        code = st.session_state.code_input
        model_name = st.session_state.model_choice

        if not code.strip():
            log("코드를 입력하세요.", "error")
            st.session_state.toggle = False
            return

        openai_key, anthropic_key = get_api_keys()
        config = MODELS[model_name]

        if config["provider"] == "openai" and not openai_key:
            log("OpenAI API 키가 없습니다. Secrets를 확인하세요.", "error")
            st.session_state.toggle = False
            return

        if config["provider"] == "anthropic" and not anthropic_key:
            log("Anthropic API 키가 없습니다. Secrets를 확인하세요.", "error")
            st.session_state.toggle = False
            return

        st.session_state.running = True
        st.session_state.cycles = 0
        st.session_state.logs = []

        t = threading.Thread(
            target=loop_worker,
            args=(code, model_name),
            daemon=True,
        )
        t.start()
        log("루프 시작...", "success")
    else:
        st.session_state.running = False
        log("사용자가 중지함", "warn")


# ─── 메인 UI ─────────────────────────────────────────────────
def main():
    init()
    openai_key, anthropic_key = get_api_keys()

    key_status = []
    if openai_key:
        key_status.append("OpenAI ✓")
    if anthropic_key:
        key_status.append("Anthropic ✓")

    st.markdown("<h1 style='text-align:center;'>⚡ 자동개발루프</h1>", unsafe_allow_html=True)

    if key_status:
        st.caption(f"연결됨: {' | '.join(key_status)}")
    else:
        st.error("API 키가 설정되지 않았습니다. Streamlit Cloud > Settings > Secrets에서 설정하세요.")
        st.code("""
OPENAI_API_KEY = "sk-proj-xxxxx"
ANTHROPIC_API_KEY = "sk-ant-xxxxx"
        """)
        return

    st.markdown(
        "<p style='text-align:center; color:#6b7a8d;'>코드를 넣고 버튼 하나로 자동 개선</p>",
        unsafe_allow_html=True,
    )

    st.toggle(
        " ", value=st.session_state.running, key="toggle",
        on_change=on_toggle, label_visibility="collapsed",
    )

    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("상태", "실행 중" if st.session_state.running else "대기 중")
    with c2:
        st.metric("단계", st.session_state.stage)
    with c3:
        st.metric("사이클", st.session_state.cycles)

    st.divider()

    available_models = []
    for name, cfg in MODELS.items():
        if cfg["provider"] == "openai" and openai_key:
            available_models.append(name)
        elif cfg["provider"] == "anthropic" and anthropic_key:
            available_models.append(name)

    st.selectbox(
        "모델 선택", available_models,
        key="model_choice", disabled=st.session_state.running,
    )

    st.text_area(
        "코드 입력", height=200, key="code_input",
        placeholder="여기에 개선할 코드를 붙여넣으세요...",
        disabled=st.session_state.running,
    )

    st.divider()

    st.markdown("### 📋 로그")

    if st.session_state.logs:
        html = '<div class="log-box">'
        for l in reversed(st.session_state.logs):
            color = {
                "info": "#e4e8ef",
                "success": "#00d4aa",
                "error": "#ff4757",
                "warn": "#ffa502",
            }.get(l["level"], "#e4e8ef")
            html += f'<div style="color:{color}"><span style="color:#6b7a8d">{l["t"]}</span> {l["msg"]}</div>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("로그가 여기에 표시됩니다")

    if "final_code" in st.session_state and st.session_state.final_code:
        st.divider()
        st.markdown("### ✅ 최종 결과")
        st.code(st.session_state.final_code, language="python")

    if st.session_state.running:
        time.sleep(1)
        st.rerun()


if __name__ == "__main__":
    main()
