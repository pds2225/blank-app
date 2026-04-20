import streamlit as st
import time
import threading
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None

st.set_page_config(page_title="자동개발루프", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .stApp { background: #0a0e14; }
    div[data-testid="stMetric"] {
        background: #111820;
        border: 1px solid #2a3444;
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label { color: #6b7a8d !important; }
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

if "running" not in st.session_state:
    st.session_state.running = False
if "stage" not in st.session_state:
    st.session_state.stage = "대기 중"
if "cycles" not in st.session_state:
    st.session_state.cycles = 0
if "logs" not in st.session_state:
    st.session_state.logs = []
if "final_code" not in st.session_state:
    st.session_state.final_code = ""

def log(msg, level="info"):
    st.session_state.logs.append({
        "t": datetime.now().strftime("%H:%M:%S"),
        "msg": msg,
        "level": level,
    })
    if len(st.session_state.logs) > 200:
        st.session_state.logs = st.session_state.logs[-200:]

def call_ai(prompt, api_key, model="gpt-4o"):
    if not openai:
        return False, "openai 패키지가 설치되지 않았습니다."
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 전문 개발자입니다. 코드를 분석하고 개선합니다. 개선된 전체 코드만 반환하세요."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return True, response.choices[0].message.content
    except Exception as e:
        return False, str(e)

def run_cycle(code, api_key, model):
    stages = [
        ("하드닝", "다음 코드를 보안, 성능, 가독성 관점에서 개선하세요. 전체 코드를 반환하세요.\n\n"),
        ("디버그", "다음 코드의 버그를 찾아 수정하세요. 전체 코드를 반환하세요.\n\n"),
    ]
    current = code
    for name, prefix in stages:
        if not st.session_state.running:
            return None
        st.session_state.stage = name
        log(f"[{name}] 시작...", "info")
        ok, result = call_ai(prefix + current, api_key, model)
        if ok:
            log(f"[{name}] 완료", "success")
            current = result
        else:
            log(f"[{name}] 실패: {result[:100]}", "error")
            return None
        time.sleep(1)
    return current

def worker(code, api_key, model):
    log("루프 시작", "success")
    cur = code
    while st.session_state.running and st.session_state.cycles < 10:
        st.session_state.cycles += 1
        log(f"=== 사이클 {st.session_state.cycles} ===", "info")
        r = run_cycle(cur, api_key, model)
        if r is None:
            break
        cur = r
        time.sleep(2)
    st.session_state.running = False
    st.session_state.stage = "대기 중"
    st.session_state.final_code = cur
    log("루프 종료", "warn")

st.markdown("<h1 style='text-align:center'>⚡ 자동개발루프</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#6b7a8d'>코드 넣고 ON 누르면 자동 개선</p>", unsafe_allow_html=True)

def on_toggle():
    if st.session_state.toggle:
        code = st.session_state.get("code_input", "")
        key = st.session_state.get("api_key", "")
        if not code.strip():
            log("코드를 입력하세요", "error")
            st.session_state.toggle = False
            return
        if not key.strip():
            log("API 키를 입력하세요", "error")
            st.session_state.toggle = False
            return
        st.session_state.running = True
        st.session_state.cycles = 0
        st.session_state.logs = []
        st.session_state.final_code = ""
        model = st.session_state.get("model", "gpt-4o")
        threading.Thread(target=worker, args=(code, key, model), daemon=True).start()
        log("시작!", "success")
    else:
        st.session_state.running = False
        log("중지", "warn")

st.toggle(" ", value=st.session_state.running, key="toggle", on_change=on_toggle, label_visibility="collapsed")
st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("상태", "실행 중" if st.session_state.running else "대기 중")
with c2:
    st.metric("단계", st.session_state.stage)
with c3:
    st.metric("사이클", st.session_state.cycles)

st.divider()

with st.expander("설정"):
    st.text_input("OpenAI API 키", type="password", key="api_key", placeholder="sk-...", disabled=st.session_state.running)
    st.selectbox("모델", ["gpt-4o", "gpt-4o-mini"], key="model", disabled=st.session_state.running)

st.text_area("코드 입력", height=200, key="code_input", placeholder="여기에 코드를 붙여넣으세요...", disabled=st.session_state.running)

st.divider()
st.markdown("### 로그")

if st.session_state.logs:
    html = '<div class="log-box">'
    for l in reversed(st.session_state.logs):
        c = {"info":"#e4e8ef","success":"#00d4aa","error":"#ff4757","warn":"#ffa502"}.get(l["level"], "#e4e8ef")
        html += f'<div style="color:{c}"><span style="color:#6b7a8d">{l["t"]}</span> {l["msg"]}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

if st.session_state.final_code:
    st.divider()
    st.markdown("### 결과")
    st.code(st.session_state.final_code)

if st.session_state.running:
    time.sleep(1)
    st.rerun()
