import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
import os

# 🌟 화면을 넓게 쓰는 와이드 레이아웃 설정
st.set_page_config(page_title="학생 글쓰기 종합 자동 평가 시스템", layout="wide")
st.markdown("""
<style>
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
    
/* 4. 기본 버튼은 차분하게, 하지만 '시계열 분석' 버튼 같은 중요 버튼은 붉은색으로! */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff; /* 기존보다 더 깔끔하게 */
        transition: all 0.3s ease;
    }
    
    /* 여기서 '시계열'이라는 글자가 포함된 버튼을 찾아 강제로 빨간색을 입힙니다 */
    div.stButton > button:contains("시계열") {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)
@st.cache_resource
def load_kiwi():
    return Kiwi()

kiwi = load_kiwi()

# 데이터 로드 함수
@st.cache_data
def load_vocab_data():
    file_path = "국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx"
    if not os.path.exists(file_path):
        st.error(f"❌ 폴더 내에서 '{file_path}' 파일을 찾을 수 없습니다. 파일명이 정확한지 확인해 주세요.")
        return {}
        
    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        target_sheet = "전체(1~5등급), 40,000개"
        if target_sheet not in sheet_names:
            target_sheet = sheet_names[0]
            
        df = pd.read_excel(file_path, sheet_name=target_sheet)
        df.columns = [str(col).strip() for col in df.columns]
        
        if '어휘' not in df.columns or '등급' not in df.columns:
            st.error("❌ 엑셀 시트에 '어휘' 또는 '등급' 열이 없습니다. 열 이름을 확인해 주세요.")
            return {}
            
        return df.set_index('어휘')['등급'].to_dict()
        
    except Exception as e:
        st.error(f"❌ 엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
        return {}

vocab_data = load_vocab_data()

# 텍스트 정밀 분석 함수
def analyze_text(text):
    char_count_no_spaces = len(text.replace(" ", "").replace("\n", ""))
    tokens = kiwi.tokenize(text)
    
    found_nouns = {}
    found_verbs = {}
    grade_words = {"1등급": {}, "2등급": {}, "3등급": {}, "4등급": {}, "5등급": {}, "등급 외": {}}
    
    total_noun_count = 0
    total_verb_count = 0
    
    for token in tokens:
        word_form = token.form
        is_noun = token.tag.startswith('N')
        is_verb = token.tag == 'VV'
        
        if is_noun:
            word_to_check = word_form
            found_nouns[word_to_check] = found_nouns.get(word_to_check, 0) + 1
            total_noun_count += 1
        elif is_verb:
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
        "nouns": found_nouns,
        "verbs": found_verbs,
        "total_nouns": total_noun_count,
        "total_verbs": total_verb_count,
        "grade_words": grade_words
    }

def format_word_dict(word_dict):
    if not word_dict:
        return "사용 없음"
    sorted_words = sorted(word_dict.items(), key=lambda x: x[1], reverse=True)
    return ", ".join([f"**{word}**({count})" for word, count in sorted_words])

# 개별 분석 결과 UI 출력 함수
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
            
    st.write("")
    
    st.markdown("""
    <div style="background-color: #f1f3f4; padding: 12px 18px; border-left: 5px solid #1a73e8; border-radius: 4px; margin-top: 15px; margin-bottom: 10px;">
        <h2 style="margin: 0; color: #202124; font-size: 24px; font-weight: bold;">📚 수준별 기초 어휘 세부 분포</h2>
    </div>
    """, unsafe_allow_html=True)
    
    desc_col, dl_col = st.columns([3, 1])
    
    with desc_col:
        st.markdown("""
        <p style="color: #5f6368; font-size: 14px; line-height: 1.6; margin: 0;">
            💡 <b>국어 기초 어휘 선정 및 어휘 등급화 목록이란?</b><br>
            국립국어원에서 한국어 교육 및 연구의 표준 지침을 제공하기 위해 일상생활과 교육 과정에서 사용 빈도가 가장 높고 필수적인 핵심 어휘들을 정밀 선정하여, 난이도와 중요도에 따라 1등급(가장 기초적)부터 5등급까지 단계별로 체계화해 놓은 국가 표준 어휘 데이터베이스입니다.
        </p>
        """, unsafe_allow_html=True)
        
    with dl_col:
        try:
            with open("국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx", "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label="📥 원본 목록 파일 다운로드",
                data=file_bytes,
                file_name="국어 기초 어휘 선정 및 어휘 등급화 목록 전체.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"dl_btn_{idx}"
            )
        except Exception:
            st.button("❌ 파일 누락 (다운로드 불가)", disabled=True, use_container_width=True, key=f"dl_btn_err_{idx}")

    for grade_name in ["1등급", "2등급", "3등급", "4등급", "5등급", "등급 외"]:
        words_in_grade = res['grade_words'][grade_name]
        total_grade_count = sum(words_in_grade.values())
        unique_word_count = len(words_in_grade)
        if total_grade_count > 0:
            with st.expander(f"{grade_name} ➔ 총 {total_grade_count}개 ({unique_word_count}종)"):
                st.write(format_word_dict(words_in_grade))

# 종합 총평 생성 함수
def generate_multi_evaluation_text(results_list):
    num_texts = len(results_list)
    first = results_list[0]
    last = results_list[-1]
    
    diff_char = last['char_count'] - first['char_count']
    diff_noun = last['total_nouns'] - first['total_nouns']
    diff_verb = last['total_verbs'] - first['total_verbs']
    
    first_graded = sum([sum(first['grade_words'][g].values()) for g in ["1등급", "2등급", "3등급", "4등급", "5등급"]])
    last_graded = sum([sum(last['grade_words'][g].values()) for g in ["1등급", "2등급", "3등급", "4등급", "5등급"]])
    diff_graded = last_graded - first_graded
    
    sentences = []
    sentences.append(f"총 {num_texts}편의 연쇄적인 글쓰기 데이터를 바탕으로 학생의 누적된 언어 표현력과 어휘 성장의 궤적을 정밀 추적하였습니다.")
    sentences.append(f"텍스트의 양적 볼륨 측면에서 첫 번째 글({first['char_count']}자) 대비 마지막 글({last['char_count']}자)에서 총 {diff_char:+}자의 분량 변화를 보이며, 생각을 구조화하고 긴 호흡으로 서술하는 문장 전개력의 변화 추이가 관찰됩니다.")
    sentences.append(f"개념의 구체성과 다채로움을 보여주는 명사 지표는 최초 {first['total_nouns']}개에서 최종 {last['total_nouns']}개로 추이({diff_noun:+}개)가 변동하였으며, 이는 글이 거듭될수록 학생이 동원하는 지식적 소재의 밀도가 달라졌음을 방증합니다.")
    sentences.append(f"서사의 생동감을 주도하는 동사 정량값은 첫 회차 {first['total_verbs']}개에서 정착 회차 {last['total_verbs']}개로 변화({diff_verb:+}개)하여, 상황을 입체적으로 풀어내는 진술의 역동성 발달 경로를 투영합니다.")
    sentences.append(f"더불어 국립국어원 규정 등급별(1~5등급) 기초 어휘의 전반적인 누적 활용 빈도는 초기 {first_graded}회에서 말기 {last_graded}회로 변화({diff_graded:+}회) 양상을 보였습니다.")
    
    if diff_char >= 0 and diff_graded >= 0:
        sentences.append("정량적 지표의 우상향 흐름과 수준별 어휘 활용의 다변화가 유기적으로 맞물린 점으로 보아, 회차가 거듭될수록 학생의 자기표현 역량이 양적·질적으로 완연하게 성숙했음을 확연히 보여줍니다.")
    elif diff_char < 0 and diff_graded >= 0:
        sentences.append("전체 문장 성분의 군더더기는 덜어내면서도 기초 등급 어휘의 집중도가 상승한 흐름을 미루어 볼 때, 문장을 정제하고 밀도 높은 글을 완성하는 편집 능력이 고도화된 것으로 파악됩니다.")
    else:
        sentences.append("각 회차별 지표의 굴곡과 변화 포인트를 면밀히 분석한 결과, 제시된 글쓰기 주제나 환경에 따른 어휘 편차가 존재할 수 있으므로 취약한 묘사 영역을 보완하는 맞춤형 피드백 지도를 권장합니다.")
        
    sentences.append("향후 지속적인 어휘 도출 훈련과 맥락 중심의 작문 피드백을 병행하여 제공한다면, 독창적이고 균형 잡힌 글쓰기 역량을 더욱 공고히 확립할 것으로 기대됩니다.")
    
    return " ".join(sentences)

# ==========================================
# 메인 UI 구성
# ==========================================
st.title("📝 학생 글쓰기 종합 자동 평가 시스템")
st.write("평가할 글의 개수를 설정하고, 단편 진단부터 다회차 성장 추적까지 한 번에 관리하세요.")
st.divider()

num_texts = st.number_input("평가할 글의 총 개수를 입력하세요.", min_value=1, max_value=10, value=1, step=1)
st.write("---")

# 글의 개수 변화 감지 및 기존 저장 데이터 초기화 로직
if "prev_num_texts" not in st.session_state:
    st.session_state["prev_num_texts"] = num_texts

if st.session_state["prev_num_texts"] != num_texts:
    for k in list(st.session_state.keys()):
        if k.startswith("res_") or k == "compare_results":
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
        text_val = st.text_area(
            f"{i+1}번째 글 입력란", 
            height=400, 
            key=f"text_{i}", 
            label_visibility="collapsed", 
            placeholder=f"{i+1}번째 글을 여기에 붙여넣으세요..."
        )
        input_texts.append(text_val)
        
        if st.button(f"✨ {i+1}번째 글쓰기 분석 및 평가하기", key=f"btn_eval_{i}"):
            if text_val.strip():
                with st.spinner(f"{i+1}번째 글을 정밀 분석 중입니다..."):
                    # 💡 임시 보관이 아닌 사물함(session_state)에 저장합니다.
                    st.session_state[f"res_{i}"] = analyze_text(text_val)
            else:
                st.warning("분석할 텍스트를 먼저 입력해 주세요.")
                
        # 💡 사물함에 데이터가 들어있다면, 새로고침(Rerun)이 일어나도 상시 노출합니다.
        if f"res_{i}" in st.session_state:
            st.divider()
            c_type = "info" if i % 2 == 0 else "success"
            display_individual_results(st.session_state[f"res_{i}"], f"📊 {i+1}번째 글 개별 분석 결과", c_type, idx=i)

# 시계열 성장 추이 분석 리포트 출력
if compare_btn:
    if all(text.strip() for text in input_texts):
        with st.spinner("전체 회차의 글을 시계열로 비교 분석 중입니다..."):
            # 💡 시계열 비교 결과도 사물함에 저장합니다.
            st.session_state["compare_results"] = [analyze_text(text) for text in input_texts]
    else:
        st.error("입력되지 않은 글이 있습니다. 모든 탭에 글을 채워주신 후 다시 버튼을 눌러주세요.")

# 💡 사물함에 시계열 결과가 존재하면 상시 유지 및 렌더링
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
            "동사 수": res["total_verbs"],
            "1등급 어휘": sum(res["grade_words"]["1등급"].values()),
            "2등급 어휘": sum(res["grade_words"]["2등급"].values()),
            "3등급 어휘": sum(res["grade_words"]["3등급"].values()),
            "4등급 어휘": sum(res["grade_words"]["4등급"].values()),
            "5등급 어휘": sum(res["grade_words"]["5등급"].values()),
        })
    
    chart_df = pd.DataFrame(trends, index=[f"{i+1}회차" for i in range(num_texts)])
    
    layout_col1, layout_col2 = st.columns([1.1, 1])
    
    with layout_col1:
        st.write("**[회차별 지표 변동 꺾은선 그래프]**")
        st.line_chart(chart_df)
        
    with layout_col2:
        st.write("**[AI 구체적 서술형 종합 총평]**")
        multi_eval_message = generate_multi_evaluation_text(results_list)
        st.warning(multi_eval_message)
        
    st.divider()
    st.header("🔍 각 회차별 상세 데이터 리포트")
    result_tabs = st.tabs([f"{i+1}번째 글 상세자료" for i in range(num_texts)])
    
    for i, r_tab in enumerate(result_tabs):
        with r_tab:
            c_type = "success" if i % 2 == 0 else "info"
            display_individual_results(results_list[i], f"📝 {i+1}번째 제출 원문 분석", c_type, idx=f"multi_{i}")
