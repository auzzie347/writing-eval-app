import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os
from google import genai # 💡 새로운 최신 구글 라이브러리로 변경!

# ==========================================
# 🌟 API 키 설정 (스트림릿 Secrets 활용)
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
st.set_page_config(page_title="학생 글쓰기 종합 자동 평가 시스템", layout="wide")

st.markdown("""
<style>
    /* 0. 폰트 적용 (모던하고 깔끔한 Noto Sans) */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif !important;
    }

    /* 1. 상단 메뉴 및 헤더 숨기기 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* 2. 글 입력칸(Text Area) 디자인 고급화 */
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 2px solid #eef0f6 !important;
        box-shadow: inset 2px 2px 5px rgba(0,0,0,0.02) !important;
        padding: 15px !important;
        font-size: 16px !important;
        transition: border-color 0.3s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #1A73E8 !important;
        box-shadow: 0 0 0 2px rgba(26,115,232,0.2) !important;
    }
    
    /* 3. 분석 결과 카드(Metric) 입체화 */
    div[data-testid="metric-container"] {
        background-color: #ffffff !important;
        border: 1px solid #eef0f6 !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.04) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="metric-container"]:hover {
        box-shadow: 0px 8px 15px rgba(0,0,0,0.08) !important;
        transform: translateY(-3px) !important;
    }
    
    /* 4. 버튼 디자인 */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }

    /* 시계열 버튼 (진보라 -> 빨강 호버) */
    button[kind="secondary"]:has(span:contains("시계열")) {
        background-color: #7E57C2 !important;
        color: white !important;
        border: none !important;
    }
    button[kind="secondary"]:has(span:contains("시계열")):hover {
        background-color: #FF4B4B !important;
        color: white !important;
    }

    /* 분석 버튼 (흰색 바탕) */
    button[kind="secondary"]:not(:has(span:contains("시계열"))) {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #e0e0e0 !important;
    }
    button[kind="secondary"]:not(:has(span:contains("시계열"))):hover {
        border: 1px solid #7E57C2 !important;
        color: #7E57C2 !important;
    }
</style>
""", unsafe_allow_html=True)

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
        if '어휘' not in df.columns or '등급' not in df.columns: return {}
        return df.set_index('어휘')['등급'].to_dict()
    except:
        return {}

vocab_data = load_vocab_data()

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
        "char_count": char_count_no_spaces,
        "nouns": found_nouns, "verbs": found_verbs,
        "total_nouns": total_noun_count, "total_verbs": total_verb_count,
        "grade_words": grade_words
    }

def format_word_dict(word_dict):
    if not word_dict: return "사용 없음"
    sorted_words = sorted(word_dict.items(), key=lambda x: x[1], reverse=True)
    return ", ".join([f"**{word}**({count})" for word, count in sorted_words])

# ==========================================
# 🌟 AI 평가문 생성 로직 (새로운 GenAI SDK 적용)
# ==========================================
def generate_ai_multi_evaluation(results_list):
    if not API_KEY_EXISTS:
        return "⚠️ API 키가 설정되지 않아 AI 종합 총평을 생성할 수 없습니다. (Settings > Secrets에서 GEMINI_API_KEY를 설정해주세요.)"
    
    num_texts = len(results_list)
    first = results_list[0]
    last = results_list[-1]
    
    prompt = f"""
    학생이 작성한 총 {num_texts}편의 연쇄적인 글쓰기 형태소 분석 데이터입니다.

    [첫 번째 글 데이터]
    - 글자 수: {first['char_count']}자 / 명사: {first['total_nouns']}개 / 동사: {first['total_verbs']}개

    [가장 최근 글 데이터]
    - 글자 수: {last['char_count']}자 / 명사: {last['total_nouns']}개 / 동사: {last['total_verbs']}개

    초등학생 아이들의 성장을 가장 가까이서 지켜보는 따뜻한 선생님의 어조로, 위 데이터의 양적 변화와 어휘력의 발전을 토대로 학생의 성장을 칭찬하고 앞으로의 글쓰기를 격려하는 종합 평가문(300자 내외)을 부드럽고 다정한 말투로 작성해 주세요. (기계적인 수치 나열보다는 의미를 짚어주세요.)
    """
    try:
        # 새로운 라이브러리 문법으로 변경됨
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"⚠️ AI 생성 중 오류가 발생했습니다: {e}"

def generate_ai_individual_feedback(res):
    if not API_KEY_EXISTS:
        return "⚠️ API 키를 설정해주세요."
    
    prompt = f"""
    학생이 방금 작성한 단편 글의 분석 데이터입니다.
    - 글자 수: {res['char_count']}자
    - 주요 명사: {list(res['nouns'].keys())[:5]} 등 총 {res['total_nouns']}개
    - 주요 동사: {list(res['verbs'].keys())[:5]} 등 총 {res['total_verbs']}개
    
    초등학생을 가르치는 다정한 선생님의 관점에서, 사용된 어휘를 바탕으로 아이가 어떤 재미있는 생각을 글로 표현했는지 칭찬하고 북돋아주는 짧은 피드백(150자 내외)을 작성해 주세요.
    """
    try:
        # 새로운 라이브러리 문법으로 변경됨
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"오류 발생: {e}"

# ==========================================
# 🌟 개별 결과 출력 및 UI
# ==========================================
def display_individual_results(res, title, container_type="info", idx=0):
    if container_type == "info": st.info(f"### {title}")
    else: st.success(f"### {title}")
        
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
            
    st.markdown("""
    <div style="background-color: #f1f3f4; padding: 12px 18px; border-left: 5px solid #1a73e8; border-radius: 4px; margin-top: 15px; margin-bottom: 10px;">
        <h2 style="margin: 0; color: #202124; font-size: 24px; font-weight: bold;">📚 수준별 기초 어휘 세부 분포</h2>
    </div>
    """, unsafe_allow_html=True)
    
    desc_col, dl_col = st.columns([3, 1])
    with desc_col:
        st.markdown("""
        <p style="color: #5f6368; font-size: 14px; margin: 0;">
            💡 <b>국어 기초 어휘 선정 및 어휘 등급화 목록이란?</b><br>
            국립국어원 표준 지침에 따라 1등급(가장 기초적)부터 5등급까지 체계화된 어휘 데이터베이스입니다.
        </p>
        """, unsafe_allow_html=True)
        
    for grade_name in ["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]:
        words_in_grade = res['grade_words'][grade_name]
        total_grade_count = sum(words_in_grade.values())
        if total_grade_count > 0:
            with st.expander(f"{grade_name} ➔ 총 {total_grade_count}개 ({len(words_in_grade)}종)"):
                st.write(format_word_dict(words_in_grade))
                
    # 개별 AI 평가문 버튼
    st.write("---")
    if st.button(f"🤖 {title} 기반 AI 맞춤형 코멘트 생성하기", key=f"ai_btn_{idx}"):
        with st.spinner("선생님의 마음으로 따뜻한 코멘트를 작성하고 있습니다..."):
            ai_feedback = generate_ai_individual_feedback(res)
            st.success(f"**💌 AI 선생님의 코멘트:**\n\n{ai_feedback}")

# ==========================================
# 🌟 메인 화면 구성
# ==========================================
st.title("📝 학생 글쓰기 종합 자동 평가 시스템")
st.write("평가할 글의 개수를 설정하고, 단편 진단부터 다회차 성장 추적까지 한 번에 관리하세요.")

if not API_KEY_EXISTS:
    st.warning("⚠️ **현재 AI API 키가 연결되어 있지 않습니다.** 데이터 수치 분석은 정상 작동하지만, AI 평가문 생성 기능을 위해 추후 `GEMINI_API_KEY`를 등록해주세요.")

st.divider()

num_texts = st.number_input("평가할 글의 총 개수를 입력하세요.", min_value=1, max_value=10, value=1, step=1)
st.write("---")

if "prev_num_texts" not in st.session_state:
    st.session_state["prev_num_texts"] = num_texts

if st.session_state["prev_num_texts"] != num_texts:
    for k in list(st.session_state.keys()):
        if k.startswith("res_") or k == "compare_results" or k == "ai_multi_eval":
            del st.session_state[k]
    st.session_state["prev_num_texts"] = num_texts

compare_btn = False
if num_texts >= 2:
    compare_btn = st.button("📈 시계열 글쓰기 역량 성장 리포트 분석하기", type="primary", use_container_width=True)
    st.info("⬇️ 아래의 탭에 각각의 글을 입력한 후, 위의 버튼을 누르면 전체 성장 추이를 한눈에 볼 수 있습니다.")
else:
    st.info("⬇️ 아래 입력칸에 글을 넣고 분석 버튼을 눌러주세요.")

tabs = st.tabs([f"{i+1}번째 글" for i in range(num_texts)])
input_texts = []

for i, tab in enumerate(tabs):
    with tab:
        text_val = st.text_area(f"{i+1}번째 글", height=300, key=f"text_{i}", label_visibility="collapsed", placeholder=f"{i+1}번째 글을 붙여넣으세요...")
        input_texts.append(text_val)
        
        if st.button(f"✨ {i+1}번째 글쓰기 분석 및 평가하기", key=f"btn_eval_{i}"):
            if text_val.strip():
                with st.spinner("정밀 분석 중입니다..."):
                    st.session_state[f"res_{i}"] = analyze_text(text_val)
            else:
                st.warning("분석할 텍스트를 먼저 입력해 주세요.")
                
        if f"res_{i}" in st.session_state:
            st.divider()
            c_type = "info" if i % 2 == 0 else "success"
            display_individual_results(st.session_state[f"res_{i}"], f"📊 {i+1}번째", c_type, idx=i)

if compare_btn:
    if all(text.strip() for text in input_texts):
        with st.spinner("글을 비교 분석하고 AI 성장 리포트를 작성 중입니다..."):
            results_list = [analyze_text(text) for text in input_texts]
            st.session_state["compare_results"] = results_list
            # 시계열 평가문은 누를 때 한 번만 생성하여 저장해둡니다.
            st.session_state["ai_multi_eval"] = generate_ai_multi_evaluation(results_list)
    else:
        st.error("입력되지 않은 글이 있습니다. 모든 탭에 글을 채워주세요.")

if "compare_results" in st.session_state:
    results_list = st.session_state["compare_results"]
    st.divider()
    st.header("📈 누적 역량 성장 리포트")
    st.subheader("📉 주요 글쓰기 지표 시계열 변화 곡선")
    
    trends = []
    for i, res in enumerate(results_list):
        trends.append({
            "글자 수": res["char_count"],
            "명사 수": res["total_nouns"],
            "동사 수": res["total_verbs"]
        })
    chart_df = pd.DataFrame(trends, index=[f"{i+1}회차" for i in range(num_texts)])
    
    layout_col1, layout_col2 = st.columns([1.1, 1])
    with layout_col1:
        st.write("**[회차별 지표 변동 꺾은선 그래프]**")
        st.line_chart(chart_df)
    with layout_col2:
        st.write("**[🤖 AI 맞춤형 종합 총평]**")
        st.warning(st.session_state.get("ai_multi_eval", "평가문이 없습니다."))
        
    st.divider()
    st.header("🔍 상세 리포트")
    result_tabs = st.tabs([f"{i+1}번째 상세" for i in range(num_texts)])
    for i, r_tab in enumerate(result_tabs):
        with r_tab:
            display_individual_results(results_list[i], f"📝 {i+1}번째 제출", "success", idx=f"multi_{i}")
