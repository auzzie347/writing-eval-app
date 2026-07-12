import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os
from google import genai  # 최신 라이브러리 사용

# ==========================================
# 🌟 모델 및 API 설정
# ==========================================
MODEL_NAME = "models/gemini-2.5-flash"
client = None
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 🌟 기본 설정 및 CSS 디자인
# ==========================================
st.set_page_config(page_title="학생 글쓰기 종합 자동 평가 시스템", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    .stTextArea textarea { border-radius: 12px !important; border: 2px solid #eef0f6 !important; padding: 15px !important; font-size: 16px !important; }
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌟 데이터 및 분석 엔진 로드
# ==========================================
@st.cache_resource
def load_kiwi(): return Kiwi()
kiwi = load_kiwi()

@st.cache_data
def load_vocab_data():
    file_path = "국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx"
    if not os.path.exists(file_path): return {}
    try:
        xl = pd.ExcelFile(file_path)
        df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0])
        df.columns = [str(col).strip() for col in df.columns]
        return df.set_index('어휘')['등급'].to_dict()
    except: return {}

vocab_data = load_vocab_data()

def analyze_text(text):
    tokens = kiwi.tokenize(text)
    found_nouns, found_verbs = {}, {}
    grade_words = {f"{i}등급": {} for i in range(1, 6)}
    grade_words["등급 외"] = {}
    total_noun = total_verb = 0
    
    for token in tokens:
        word = token.form
        word_check = word + ("다" if token.tag == 'VV' else "")
        if token.tag.startswith('N'):
            found_nouns[word] = found_nouns.get(word, 0) + 1
            total_noun += 1
        elif token.tag == 'VV':
            found_verbs[word_check] = found_verbs.get(word_check, 0) + 1
            total_verb += 1
        else: continue
        
        grade = vocab_data.get(word) or vocab_data.get(word_check)
        grade_key = str(grade).strip() if grade and str(grade).strip() in grade_words else "등급 외"
        grade_words[grade_key][word_check] = grade_words[grade_key].get(word_check, 0) + 1
            
    return {"char_count": len(text.replace(" ", "").replace("\n", "")), "nouns": found_nouns, 
            "verbs": found_verbs, "total_nouns": total_noun, "total_verbs": total_verb, "grade_words": grade_words}

# ==========================================
# 🌟 최신 SDK 기반 AI 호출 함수
# ==========================================
def ask_gemini(prompt):
    if not client: return "⚠️ API 키가 설정되지 않았습니다."
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e: return f"⚠️ AI 생성 오류: {e}"

# ==========================================
# 🌟 결과 UI 출력 함수
# ==========================================
def display_individual_results(res, title, idx):
    st.info(f"### {title}")
    c1, c2, c3 = st.columns(3)
    c1.metric("글자 수", f"{res['char_count']}자")
    c2.metric("명사", f"{res['total_nouns']}개")
    c3.metric("동사", f"{res['total_verbs']}개")
    
    st.subheader("📚 수준별 기초 어휘 분포")
    cols = st.columns(6)
    grades = ["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]
    for i, g in enumerate(grades):
        count = sum(res['grade_words'][g].values())
        cols[i].metric(g, f"{count}개")
        if count > 0:
            with st.expander(f"📖 {g} 상세 보기"):
                st.write(", ".join([f"**{w}**({c})" for w, c in res['grade_words'][g].items()]))
                
    if st.button(f"🤖 {title} 기반 AI 코멘트 생성", key=f"ai_{idx}"):
        with st.spinner("선생님의 마음으로 분석 중..."):
            prompt = f"학생 글 분석 데이터: {res}. 다정한 선생님 어조로 피드백 작성해줘."
            st.success(ask_gemini(prompt))

# ==========================================
# 🌟 메인 화면 (기존 로직 유지)
# ==========================================
st.title("📝 학생 글쓰기 종합 자동 평가 시스템")
num_texts = st.number_input("평가할 글의 개수", min_value=1, value=1)
tabs = st.tabs([f"{i+1}번째" for i in range(num_texts)])

for i, tab in enumerate(tabs):
    with tab:
        text = st.text_area(f"{i+1}번째 글 입력", key=f"text_{i}")
        if st.button(f"분석", key=f"btn_{i}"):
            if text: display_individual_results(analyze_text(text), f"{i+1}번째 결과", i)
