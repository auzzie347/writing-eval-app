import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os
import google.generativeai as genai

# ==========================================
# 🌟 모델명 설정 (찾아낸 정확한 경로명 사용)
# ==========================================
MODEL_NAME = 'models/gemini-2.5-flash'

# ==========================================
# 🌟 API 키 설정
# ==========================================
API_KEY_EXISTS = False
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        API_KEY_EXISTS = True
except Exception:
    pass

# ==========================================
# 🌟 기본 설정 및 CSS 디자인
# ==========================================
st.set_page_config(page_title="학생 글쓰기 종합 자동 평가 시스템", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌟 데이터 로드
# ==========================================
@st.cache_resource
def load_kiwi():
    return Kiwi()

kiwi = load_kiwi()

@st.cache_data
def load_vocab_data():
    file_path = "국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx"
    if not os.path.exists(file_path): return {}
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip() for col in df.columns]
        return df.set_index('어휘')['등급'].to_dict()
    except: return {}

vocab_data = load_vocab_data()

# ==========================================
# 🌟 핵심 분석 로직 (매칭 보정 강화)
# ==========================================
def analyze_text(text):
    char_count = len(text.replace(" ", "").replace("\n", ""))
    tokens = kiwi.tokenize(text)
    
    found_nouns, found_verbs = {}, {}
    grade_words = {f"{i}등급": {} for i in range(1, 6)}
    grade_words["등급 외"] = {}
    
    total_noun_count = total_verb_count = 0
    
    for token in tokens:
        word_to_check = token.form + ("다" if token.tag == 'VV' else "")
        if token.tag.startswith('N'):
            found_nouns[word_to_check] = found_nouns.get(word_to_check, 0) + 1
            total_noun_count += 1
        elif token.tag == 'VV':
            found_verbs[word_to_check] = found_verbs.get(word_to_check, 0) + 1
            total_verb_count += 1
        
        # 등급 매칭 (공백/대소문자 제거 후 비교)
        grade = vocab_data.get(token.form) or vocab_data.get(word_to_check)
        if grade:
            grade_key = str(grade).strip()
            if grade_key in grade_words:
                grade_words[grade_key][word_to_check] = grade_words[grade_key].get(word_to_check, 0) + 1
            else:
                grade_words["등급 외"][word_to_check] = grade_words["등급 외"].get(word_to_check, 0) + 1
        elif token.tag.startswith('N') or token.tag == 'VV':
            grade_words["등급 외"][word_to_check] = grade_words["등급 외"].get(word_to_check, 0) + 1
            
    return {"char_count": char_count, "nouns": found_nouns, "verbs": found_verbs, 
            "total_nouns": total_noun_count, "total_verbs": total_verb_count, "grade_words": grade_words}

# ==========================================
# 🌟 AI 평가 로직 (직접 지정)
# ==========================================
def get_ai_response(prompt):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 생성 오류: {e}"

# (이후 display_individual_results 및 UI 코드는 이전과 동일하게 유지하시면 됩니다.)
