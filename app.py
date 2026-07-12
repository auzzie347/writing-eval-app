import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os
from google import genai  # 최신 라이브러리 (pip install google-genai)

# ==========================================
# 🌟 모델 및 API 설정 (최신 표준 방식)
# ==========================================
MODEL_NAME = "models/gemini-2.5-flash"  # curl로 확인한 정확한 경로명

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
# 🌟 형태소 분석 및 등급 분류 로직
# ==========================================
def analyze_text(text):
    tokens = kiwi.tokenize(text)
    found_nouns, found_verbs = {}, {}
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
# 🌟 AI 평가 로직 (최신 Client 방식)
# ==========================================
def ask_gemini(prompt):
    if not client: return "⚠️ API 키가 설정되지 않았습니다."
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e: return f"⚠️ AI 생성 오류: {e}"

# ==========================================
# 🌟 결과 출력 UI
# ==========================================
def display_results(res, title, idx):
    st.info(f"### {title}")
    c1, c2, c3 = st.columns(3)
    c1.metric("글자 수", f"{res['char_count']}자")
    c2.metric("명사", f"{res['total_nouns']}개")
    c3.metric("동사", f"{res['total_verbs']}개")
    
    st.subheader("📚 수준별 기초 어휘 분포")
    cols = st.columns(6)
    for i, g in enumerate(["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]):
        count = sum(res['grade_words'][g].values())
        cols[i].metric(g, f"{count}개")
        if count > 0:
            with st.expander(f"📖 {g} 상세"):
                st.write(", ".join([f"**{w}**({c})" for w, c in res['grade_words'][g].items()]))
                
    if st.button(f"🤖 AI 코멘트 생성", key=f"ai_{idx}"):
        with st.spinner("생성 중..."):
            st.success(ask_gemini(f"다음 데이터 분석 결과에 대해 다정한 선생님 어조로 피드백해줘: {res}"))

# ==========================================
# 🌟 메인 화면
# ==========================================
st.title("📝 학생 글쓰기 자동 평가 시스템")
text = st.text_area("글 입력")
if st.button("분석 실행"):
    if text.strip(): display_results(analyze_text(text), "분석 결과", 0)
    else: st.warning("글을 입력하세요.")
