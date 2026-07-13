import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os
from google import genai

# ==========================================
# 🌟 API 키 설정
# ==========================================
API_KEY_EXISTS = False
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY_EXISTS = True
except Exception:
    pass

# ==========================================
# 🌟 기본 설정 및 CSS 디자인
# ==========================================
st.set_page_config(page_title="학생 글쓰기 종합 자동 평가 시스템", page_icon="📝", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
    .stApp { background: linear-gradient(180deg, #F7F9FD 0%, #EEF3FA 100%) !important; }
    #MainMenu, footer, header { visibility: hidden !important; }
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    h1 {
        font-family: 'Gowun Dodum', sans-serif !important;
        color: #1F2D4E !important;
        font-size: 2.3rem !important;
        letter-spacing: -0.5px !important;
    }
    h2, h3 { font-family: 'Gowun Dodum', sans-serif !important; color: #2A3A63 !important; }
    .subtitle { color: #5C6B8A; font-size: 1.02rem; margin-top: -8px; margin-bottom: 6px; }

    /* 리포트 화면 헤더 배지 */
    .report-header {
        background: linear-gradient(135deg, #1F2D4E 0%, #2A3A63 100%);
        color: white !important;
        padding: 28px 36px;
        border-radius: 18px;
        margin-bottom: 28px;
        box-shadow: 0 8px 24px rgba(31,45,78,0.18);
    }
    .report-header h1 { color: white !important; font-size: 1.9rem !important; margin: 0 !important; }
    .report-header p { color: #BFD0EE !important; margin: 6px 0 0 0 !important; font-size: 1rem; }

    .stTextArea textarea {
        border-radius: 14px !important; border: 2px solid #E2E8F4 !important;
        background-color: #FFFFFF !important; box-shadow: 0 2px 8px rgba(31,45,78,0.04) !important;
        padding: 16px !important; font-size: 16px !important; line-height: 1.7 !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #3E5C9A !important;
        box-shadow: 0 0 0 3px rgba(62,92,154,0.15) !important;
    }
    div[data-testid="stNumberInput"] input { border-radius: 10px !important; }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important; border: 1px solid #E6ECF6 !important;
        padding: 18px 22px !important; border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(31,45,78,0.05) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 10px 22px rgba(31,45,78,0.10) !important;
        transform: translateY(-3px) !important;
    }
    div[data-testid="stMetric"] label { color: #5C6B8A !important; font-weight: 500 !important; }
    div[data-testid="stMetricValue"] { color: #1F2D4E !important; font-family: 'Gowun Dodum', sans-serif !important; }

    .stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        padding: 11px 26px !important; transition: all 0.25s ease !important;
    }
    /* 🔴 시계열 분석 버튼 (primary) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #E63946 0%, #C1121F 100%) !important;
        color: #FFFFFF !important; border: none !important;
        box-shadow: 0 4px 12px rgba(230,57,70,0.35) !important; font-size: 1.05rem !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #C1121F 0%, #9E0E19 100%) !important;
        box-shadow: 0 6px 18px rgba(230,57,70,0.45) !important;
        transform: translateY(-2px) !important;
    }
    /* ⚪ 일반 버튼 */
    button[kind="secondary"] {
        background-color: #FFFFFF !important; color: #2A3A63 !important;
        border: 1.5px solid #D5DEEE !important; box-shadow: 0 2px 6px rgba(31,45,78,0.04) !important;
    }
    button[kind="secondary"]:hover {
        border-color: #3E5C9A !important; color: #3E5C9A !important;
        box-shadow: 0 4px 12px rgba(62,92,154,0.15) !important; transform: translateY(-1px) !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent !important; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF !important; border: 1px solid #E2E8F4 !important;
        border-radius: 10px 10px 0 0 !important; padding: 10px 20px !important;
        color: #5C6B8A !important; font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2A3A63 !important; color: #FFFFFF !important; border-color: #2A3A63 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important; border: 1px solid #E6ECF6 !important;
        border-radius: 12px !important; box-shadow: 0 2px 8px rgba(31,45,78,0.04) !important;
    }
    hr { border-color: #DDE5F1 !important; }

    /* 뒤로가기 버튼 강조 */
    .back-btn button {
        background-color: #FFFFFF !important; color: #1F2D4E !important;
        border: 2px solid #2A3A63 !important; font-size: 1rem !important;
        padding: 12px 30px !important;
    }
    .back-btn button:hover {
        background-color: #2A3A63 !important; color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌟 session_state 초기화
# ==========================================
if "screen" not in st.session_state:
    st.session_state["screen"] = "input"   # "input" | "report"
if "prev_num_texts" not in st.session_state:
    st.session_state["prev_num_texts"] = 1
if "student_name" not in st.session_state:
    st.session_state["student_name"] = ""

# ==========================================
# 🌟 데이터 및 분석 엔진 로드
# ==========================================
@st.cache_resource
def load_kiwi():
    return Kiwi()

kiwi = load_kiwi()

@st.cache_data
def load_vocab_data():
    file_path = "국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx"
    if not os.path.exists(file_path):
        return {}
    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        target_sheet = "전체(1~5등급), 40,000개" if "전체(1~5등급), 40,000개" in sheet_names else sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=target_sheet)
        df.columns = [str(col).strip() for col in df.columns]
        if '어휘' not in df.columns or '등급' not in df.columns:
            return {}
        return df.set_index('어휘')['등급'].to_dict()
    except:
        return {}

vocab_data = load_vocab_data()

@st.cache_data
def load_vocab_file_bytes():
    file_path = "국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx"
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return f.read()

def analyze_text(text):
    char_count_no_spaces = len(text.replace(" ", "").replace("\n", ""))
    tokens = kiwi.tokenize(text)
    found_nouns, found_verbs = {}, {}
    grade_words = {"1등급": {}, "2등급": {}, "3등급": {}, "4등급": {}, "5등급": {}, "등급 외": {}}
    total_noun_count = total_verb_count = 0

    for token in tokens:
        word_form = token.form
        if token.tag.startswith('N'):
            word_to_check = word_form
            found_nouns[word_to_check] = found_nouns.get(word_to_check, 0) + 1
            total_noun_count += 1
        elif token.tag == 'VV':
            word_to_check = word_form + "다"
            found_verbs[word_to_check] = found_verbs.get(word_to_check, 0) + 1
            total_verb_count += 1
        else:
            continue
        grade = vocab_data.get(word_to_check)
        if grade and isinstance(grade, str):
            grade_cleaned = grade.strip()
            if grade_cleaned in grade_words:
                grade_words[grade_cleaned][word_to_check] = grade_words[grade_cleaned].get(word_to_check, 0) + 1
            else:
                grade_words["등급 외"][word_to_check] = grade_words["등급 외"].get(word_to_check, 0) + 1
        else:
            grade_words["등급 외"][word_to_check] = grade_words["등급 외"].get(word_to_check, 0) + 1

    return {
        "text": text,
        "char_count": char_count_no_spaces,
        "nouns": found_nouns, "verbs": found_verbs,
        "total_nouns": total_noun_count, "total_verbs": total_verb_count,
        "grade_words": grade_words,
    }

def format_word_dict(word_dict):
    if not word_dict:
        return "사용 없음"
    sorted_words = sorted(word_dict.items(), key=lambda x: x[1], reverse=True)
    return ", ".join([f"**{word}**({count})" for word, count in sorted_words])

def grade_summary_text(res):
    parts = []
    for g in ["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]:
        cnt = sum(res["grade_words"][g].values())
        kinds = len(res["grade_words"][g])
        parts.append(f"{g} {cnt}개({kinds}종)")
    return " / ".join(parts)

# ==========================================
# 🌟 AI 평가 생성
# ==========================================
MAX_TEXT_LEN = 2500

def generate_ai_multi_evaluation(results_list, student_name=""):
    if not API_KEY_EXISTS:
        return "⚠️ API 키가 설정되지 않아 AI 종합 총평을 생성할 수 없습니다."
    num_texts = len(results_list)
    name_label = f"{student_name} 학생" if student_name.strip() else "학생"
    data_blocks = []
    for i, res in enumerate(results_list):
        excerpt = res["text"][:MAX_TEXT_LEN]
        data_blocks.append(f"""
[{i+1}번째 글]
- 글자 수(공백 제외): {res['char_count']}자
- 명사 사용량: {res['total_nouns']}개 / 동사 사용량: {res['total_verbs']}개
- 기초어휘 등급별 분포: {grade_summary_text(res)}
- 글 원문:
\"\"\"{excerpt}\"\"\"
""")
    prompt = f"""당신은 초등학생의 글쓰기 성장을 오랫동안 지도해 온 경험 많고 다정한 국어 선생님입니다.
평가 대상 학생 이름: {name_label}
{name_label}이(가) 시간 순서대로 작성한 총 {num_texts}편의 글과 형태소 분석 데이터가 아래에 있습니다.

{''.join(data_blocks)}

위 자료를 모두 종합하여, {name_label}의 글쓰기 역량 향상에 대한 구체적인 종합 평가문을 1000자 내외로 작성해 주세요.
평가문 전체에 걸쳐 '{name_label}'을(를) 자연스럽게 호명하면서 작성해 주세요.
반드시 다음 네 가지 관점을 균형 있게 담아 주세요.

1. [양적 성장] 글자 수, 명사·동사 사용량이 회차에 따라 어떻게 변화했는지, 그 변화가 갖는 의미
2. [어휘 수준] 기초어휘 등급(1~5등급) 분포를 근거로 어휘 사용 수준이 어떻게 발전했는지
3. [내용과 체계성] 각 글의 원문을 직접 읽고, 주제 표현, 생각의 깊이, 문단 구성, 글의 흐름을 구체적 문장을 예로 들어 평가
4. [앞으로의 방향] 다음 글쓰기에서 도전해 보면 좋을 점을 1~2가지 구체적으로 제안

작성 규칙:
- 따뜻하고 다정한 선생님의 말투로 작성
- 수치보다 그 의미를 해석해서 서술
- 잘한 점을 먼저 충분히 칭찬한 뒤, 개선점은 격려하는 방식으로 제안
- 전체 분량은 800자 내외(700~900자)로 작성
"""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 생성 중 오류가 발생했습니다: {e}"

def generate_ai_individual_feedback(res, student_name=""):
    if not API_KEY_EXISTS:
        return "⚠️ API 키를 설정해주세요."
    name_label = f"{student_name} 학생" if student_name.strip() else "학생"
    excerpt = res["text"][:MAX_TEXT_LEN]
    prompt = f"""당신은 초등학생의 글쓰기를 지도하는 경험 많고 다정한 국어 선생님입니다.
평가 대상 학생 이름: {name_label}
{name_label}이(가) 방금 작성한 글과 형태소 분석 데이터가 아래에 있습니다.
평가문 전체에 걸쳐 '{name_label}'을(를) 자연스럽게 호명하면서 작성해 주세요.

[분석 데이터]
- 글자 수(공백 제외): {res['char_count']}자
- 명사 사용량: {res['total_nouns']}개 / 동사 사용량: {res['total_verbs']}개
- 기초어휘 등급별 분포: {grade_summary_text(res)}

[글 원문]
\"\"\"{excerpt}\"\"\"

위 자료를 바탕으로, 이 글에 대한 선생님 총평을 1000자 내외로 작성해 주세요.
반드시 다음 네 가지 관점을 담아 주세요.

1. [양적 특징] 글자 수, 명사·동사 사용량이 보여주는 글의 특징
2. [어휘 수준] 기초어휘 등급 분포를 근거로 학생의 어휘 사용 수준 평가
3. [내용과 체계성] 원문을 직접 읽고 주제 표현, 생각의 깊이, 문단 구성, 글의 흐름을 구체적 문장을 예로 들어 평가
4. [성장 제안] 다음 글에서 시도해 보면 좋을 점 1~2가지

작성 규칙:
- 따뜻하고 다정한 선생님의 말투로 작성
- 수치의 기계적 나열이 아니라 의미를 해석해서 서술
- 잘한 점을 먼저 칭찬한 뒤, 개선점은 격려하는 방식으로
- 전체 분량은 1000자 내외(900~1100자)로 작성
"""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"오류 발생: {e}"

# ==========================================
# 🌟 공통 UI 컴포넌트
# ==========================================
def show_vocab_section_header(idx):
    """기초어휘 섹션 헤더 + 다운로드 버튼"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #FFFFFF 0%, #F2F6FC 100%); padding: 14px 20px;
                border-left: 5px solid #2A3A63; border-radius: 10px; margin-top: 18px; margin-bottom: 12px;
                box-shadow: 0 2px 8px rgba(31,45,78,0.05);">
        <h2 style="margin: 0; color: #1F2D4E; font-size: 22px; font-weight: bold; font-family: 'Gowun Dodum', sans-serif;">
            📚 수준별 기초 어휘 세부 분포
        </h2>
    </div>
    """, unsafe_allow_html=True)

    desc_col, dl_col = st.columns([2.6, 1])
    with desc_col:
        st.markdown("""
        <p style="margin: 0; line-height: 1.7;">
            <span style="color: #1F2D4E; font-size: 19px; font-weight: 700;">💡 국어 기초 어휘 선정 및 어휘 등급화 목록이란?</span><br>
            <span style="color: #3D4C6E; font-size: 17px;">국립국어원 표준 지침에 따라 1등급(가장 기초적)부터 5등급까지 체계화된 어휘 데이터베이스입니다.</span>
        </p>
        """, unsafe_allow_html=True)
    with dl_col:
        vocab_bytes = load_vocab_file_bytes()
        if vocab_bytes:
            st.download_button(
                label="📥 어휘 목록 다운로드",
                data=vocab_bytes,
                file_name="국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_btn_{idx}",
                use_container_width=True,
            )
        else:
            st.caption("⚠️ 어휘 목록 파일을 찾을 수 없습니다.")

def display_individual_results(res, title, container_type="info", idx=0):
    if container_type == "info":
        st.info(f"### {title}")
    else:
        st.success(f"### {title}")

    c1, c2, c3 = st.columns(3)
    c1.metric("글자 수 (공백 제외)", f"{res['char_count']}자")
    c2.metric("명사 사용량", f"{res['total_nouns']}개")
    c3.metric("동사 사용량", f"{res['total_verbs']}개")

    st.write("")
    n_col, v_col = st.columns(2)
    with n_col:
        with st.expander(f"📋 명사 목록 ({len(res['nouns'])}종)"):
            st.write(format_word_dict(res['nouns']))
    with v_col:
        with st.expander(f"📋 동사 목록 ({len(res['verbs'])}종)"):
            st.write(format_word_dict(res['verbs']))

    show_vocab_section_header(idx)

    for grade_name in ["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]:
        words_in_grade = res['grade_words'][grade_name]
        total_grade_count = sum(words_in_grade.values())
        if total_grade_count > 0:
            with st.expander(f"{grade_name} ➔ 총 {total_grade_count}개 ({len(words_in_grade)}종)"):
                st.write(format_word_dict(words_in_grade))

    st.write("---")
    if st.button(f"🤖 {title} 기반 AI 맞춤형 총평 생성하기", key=f"ai_btn_{idx}"):
        with st.spinner("선생님의 마음으로 글을 꼼꼼히 읽고 총평을 작성하고 있습니다..."):
            ai_feedback = generate_ai_individual_feedback(res, st.session_state.get("student_name", ""))
            st.success(f"**💌 선생님 총평:**\n\n{ai_feedback}")

# ==========================================
# 🌟 화면 1: 입력 화면
# ==========================================
def show_input_screen():
    st.title("📝 학생 글쓰기 종합 자동 평가 시스템")
    st.markdown('<p class="subtitle">평가할 글의 개수를 설정하고, 단편 진단부터 다회차 성장 추적까지 한 번에 관리하세요.</p>', unsafe_allow_html=True)

    if not API_KEY_EXISTS:
        st.warning("⚠️ **현재 AI API 키가 연결되어 있지 않습니다.**")

    st.divider()

    name_col, count_col = st.columns([2, 1])
    with name_col:
        student_name = st.text_input(
            "누구의 글을 평가하시나요?",
            value=st.session_state.get("student_name", ""),
            placeholder="예: 김민준",
            key="student_name_input",
        )
        st.session_state["student_name"] = student_name
    with count_col:
        num_texts = st.number_input(
            "평가할 글의 총 개수",
            min_value=1, max_value=10,
            value=st.session_state.get("num_texts_val", 1),
            step=1,
        )
        st.session_state["num_texts_val"] = num_texts
    st.write("---")

    # 개수가 바뀌면 결과 초기화
    if st.session_state["prev_num_texts"] != num_texts:
        for k in list(st.session_state.keys()):
            if k.startswith("res_") or k in ("compare_results", "ai_multi_eval", "input_texts_saved"):
                del st.session_state[k]
        st.session_state["prev_num_texts"] = num_texts

    # 시계열 분석 버튼 (2편 이상일 때)
    if num_texts >= 2:
        compare_btn = st.button("📈 시계열 글쓰기 역량 성장 리포트 분석하기", type="primary", use_container_width=True)
        st.info("⬇️ 아래 탭에 각각의 글을 입력한 후, 위 버튼을 누르면 성장 리포트 화면으로 이동합니다.")
    else:
        compare_btn = False
        st.info("⬇️ 아래 입력칸에 글을 넣고 분석 버튼을 눌러주세요.")

    # 탭 구성
    tabs = st.tabs([f"{i+1}번째 글" for i in range(num_texts)])
    input_texts = []

    for i, tab in enumerate(tabs):
        with tab:
            saved_text = st.session_state.get(f"text_saved_{i}", "")
            text_val = st.text_area(
                f"{i+1}번째 글", height=300, key=f"text_{i}",
                label_visibility="collapsed",
                placeholder=f"{i+1}번째 글을 붙여넣으세요...",
                value=saved_text,
            )
            input_texts.append(text_val)

            if st.button(f"✨ {i+1}번째 글쓰기 분석 및 평가하기", key=f"btn_eval_{i}"):
                if text_val.strip():
                    with st.spinner("정밀 분석 중입니다..."):
                        st.session_state[f"res_{i}"] = analyze_text(text_val)
                        st.session_state[f"text_saved_{i}"] = text_val
                else:
                    st.warning("분석할 텍스트를 먼저 입력해 주세요.")

            if f"res_{i}" in st.session_state:
                st.divider()
                c_type = "info" if i % 2 == 0 else "success"
                display_individual_results(st.session_state[f"res_{i}"], f"📊 {i+1}번째", c_type, idx=i)

    # 시계열 분석 버튼 처리 → 화면 전환
    if compare_btn:
        # 현재 입력창 값을 session_state에서 읽기
        current_texts = [st.session_state.get(f"text_{i}", "") for i in range(num_texts)]
        # text_area value는 위에서 text_val로 읽었으므로 input_texts 사용
        if all(t.strip() for t in input_texts):
            with st.spinner("글을 비교 분석하고 AI 성장 리포트를 작성 중입니다..."):
                results_list = [analyze_text(t) for t in input_texts]
                st.session_state["compare_results"] = results_list
                st.session_state["ai_multi_eval"] = generate_ai_multi_evaluation(results_list, student_name)
                st.session_state["report_num_texts"] = num_texts
                st.session_state["student_name"] = student_name
                # 입력 텍스트 저장 (돌아왔을 때 복원용)
                for i, t in enumerate(input_texts):
                    st.session_state[f"text_saved_{i}"] = t
            st.session_state["screen"] = "report"
            st.rerun()
        else:
            st.error("입력되지 않은 글이 있습니다. 모든 탭에 글을 채워주세요.")

# ==========================================
# 🌟 화면 2: 시계열 리포트 화면
# ==========================================
def show_report_screen():
    results_list = st.session_state.get("compare_results", [])
    ai_eval = st.session_state.get("ai_multi_eval", "")
    num_texts = st.session_state.get("report_num_texts", len(results_list))

    # ── 헤더 ──
    student_name = st.session_state.get("student_name", "")
    name_display = f"{student_name} 학생 · " if student_name.strip() else ""
    st.markdown(f"""
    <div class="report-header">
        <h1>📈 시계열 글쓰기 역량 성장 리포트</h1>
        <p>{name_display}총 {num_texts}편의 글을 분석한 결과입니다 · AI 종합 총평 포함</p>
    </div>
    """, unsafe_allow_html=True)

    # ── 뒤로가기 버튼 ──
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 입력 화면으로 돌아가기"):
        st.session_state["screen"] = "input"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ── 섹션 1: 꺾은선 그래프 + AI 총평 ──
    st.subheader("📉 주요 글쓰기 지표 시계열 변화")

    trends = []
    for res in results_list:
        trends.append({
            "글자 수": res["char_count"],
            "명사 수": res["total_nouns"],
            "동사 수": res["total_verbs"],
        })
    chart_df = pd.DataFrame(trends, index=[f"{i+1}회차" for i in range(num_texts)])

    graph_col, eval_col = st.columns([1.1, 1])
    with graph_col:
        st.markdown("**회차별 지표 변동 꺾은선 그래프**")
        st.line_chart(chart_df)
    with eval_col:
        st.markdown("**🤖 AI 맞춤형 종합 총평**")
        st.markdown(f"""
        <div style="background:#FFFBF0; border:1px solid #F0C040; border-left:5px solid #F0A000;
                    border-radius:12px; padding:20px 22px; font-size:15px; line-height:1.85;
                    color:#2D2A00; max-height:420px; overflow-y:auto;">
            {ai_eval.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── 섹션 2: 회차별 상세 리포트 탭 ──
    st.subheader("🔍 회차별 상세 분석")
    result_tabs = st.tabs([f"{i+1}번째 글 상세" for i in range(num_texts)])
    for i, r_tab in enumerate(result_tabs):
        with r_tab:
            display_individual_results(results_list[i], f"📝 {i+1}번째 제출", "success", idx=f"report_{i}")

    st.divider()

    # ── 하단 뒤로가기 ──
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 입력 화면으로 돌아가기", key="back_bottom"):
        st.session_state["screen"] = "input"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🌟 라우터: 화면 전환
# ==========================================
if st.session_state["screen"] == "report" and "compare_results" in st.session_state:
    show_report_screen()
else:
    show_input_screen()
