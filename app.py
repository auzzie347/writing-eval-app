import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os
from google import genai  # 최신 SDK 사용

# ==========================================
# 🌟 모델 및 API 설정
# ==========================================
MODEL_NAME = "models/gemini-2.5-flash"  # curl로 확인한 정확한 모델명

client = None
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 🌟 나머지 디자인 및 데이터 로드 (이전과 동일)
# ==========================================
st.set_page_config(page_title="학생 글쓰기 종합 자동 평가 시스템", layout="wide")
# [기존의 CSS 스타일 코드를 여기에 그대로 붙여넣으세요]

@st.cache_resource
def load_kiwi(): return Kiwi()
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
# 🌟 핵심 분석 로직 (매칭률 향상)
# ==========================================
def analyze_text(text):
    char_count = len(text.replace(" ", "").replace("\n", ""))
    tokens = kiwi.tokenize(text)
    
    found_nouns, found_verbs = {}, {}
    grade_words = {f"{i}등급": {} for i in range(1, 6)}
    grade_words["등급 외"] = {}
    
    total_noun, total_verb = 0, 0
    
    for token in tokens:
        word = token.form
        # 명사/동사 처리
        if token.tag.startswith('N'):
            found_nouns[word] = found_nouns.get(word, 0) + 1
            total_noun += 1
        elif token.tag == 'VV':
            word = word + "다"
            found_verbs[word] = found_verbs.get(word, 0) + 1
            total_verb += 1
        else: continue
        
        # 등급 매칭 (공백 제거 후 매칭)
        grade = vocab_data.get(word)
        grade_key = str(grade).strip() if grade and str(grade).strip() in grade_words else "등급 외"
        grade_words[grade_key][word] = grade_words[grade_key].get(word, 0) + 1
            
    return {"char_count": char_count, "nouns": found_nouns, "verbs": found_verbs, 
            "total_nouns": total_noun, "total_verbs": total_verb, "grade_words": grade_words}

# ==========================================
# 🌟 AI 평가 로직 (최신 Client 방식)
# ==========================================
def ask_gemini(prompt):
    if not client: return "⚠️ API 키가 설정되지 않았습니다."
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 생성 오류: {e}"

# 나머지 UI 구성 코드는 기존 코드의 display_individual_results 함수부터 
# 끝까지 그대로 가져다 붙이시면 됩니다. ask_gemini 함수만 위 내용으로 바꾸세요.
