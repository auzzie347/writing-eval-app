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
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip() for col in df.columns]
        return df.set_index('어휘')['등급'].to_dict()
    except: return {}

vocab_data = load_vocab_data()

# ==========================================
# 🌟 분석 로직 (등급별 개수 계산 포함)
# ==========================================
def analyze_text(text):
    tokens = kiwi.tokenize(text)
    found_nouns, found_verbs = {}, {}
    # 등급별 사전 초기화
    grade_words = {f"{i}등급": {} for i in range(1, 6)}
    grade_words["등급 외"] = {}
    
    total_noun, total_verb = 0, 0
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
# 🌟 AI 평가 로직
# ==========================================
def ask_gemini(prompt):
    if not client: return "⚠️ API 키 미설정"
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e: return f"⚠️ 오류: {e}"

# ==========================================
# 🌟 결과 UI 출력 (등급별 개수 포함)
# ==========================================
def display_individual_results(res, title, idx):
    st.info(f"### {title}")
    c1, c2, c3 = st.columns(3)
    c1.metric("글자 수", f"{res['char_count']}자")
    c2.metric("명사", f"{res['total_nouns']}개")
    c3.metric("동사", f"{res['total_verbs']}개")
    
    st.write("---")
    st.subheader("📚 수준별 기초 어휘 분포")
    cols = st.columns(6)
    grade_names = ["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]
    for i, g in enumerate(grade_names):
        count = sum(res['grade_words'][g].values())
        cols[i].metric(g, f"{count}개")
        if count > 0:
            with st.expander(f"상세 보기({g})"):
                st.write(", ".join([f"**{w}**({c})" for w, c in res['grade_words'][g].items()]))
                
    if st.button(f"🤖 AI 코멘트 생성", key=f"ai_{idx}"):
        feedback = ask_gemini(f"다음 데이터로 학생 피드백 작성: {res}")
        st.success(feedback)

# ==========================================
# 🌟 메인 실행
# ==========================================
st.title("📝 학생 글쓰기 종합 자동 평가 시스템")
text = st.text_area("글 입력")
if st.button("분석 실행"):
    result = analyze_text(text)
    display_individual_results(result, "분석 결과", 0)
