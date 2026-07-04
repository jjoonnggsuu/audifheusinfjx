import re
import pandas as pd
import streamlit as st
from supabase import create_client

# =========================
# 페이지 및 디자인 설정
# =========================
st.set_page_config(page_title="학생 생활습관 설문 시스템", page_icon="📘", layout="centered")

st.markdown("""
<style>
.block-container { max-width: 900px; padding-top: 2rem; }
h1 { text-align: center; color: #1f2937; font-weight: 800; }
.stForm { background-color: white; padding: 30px; border-radius: 20px; border: 1px solid #e5e7eb; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.stButton button { width: 100%; border-radius: 12px; font-size: 18px; font-weight: bold; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# =========================
# Supabase 연결
# =========================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    TABLE_NAME = st.secrets.get("TABLE_NAME", "student_survey")
except Exception:
    st.error("Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 기능 함수들
# =========================
def load_data():
    response = supabase.table(TABLE_NAME).select("*").execute()
    return pd.DataFrame(response.data)

def make_next_student_id(df):
    if df.empty or "student_id" not in df.columns: return "S001"
    max_number = 0
    for sid in df["student_id"].dropna():
        match = re.search(r"\d+", str(sid))
        if match:
            number = int(match.group())
            if number > max_number: max_number = number
    return f"S{max_number + 1:03d}"

def make_next_index(df):
    if df.empty or "index" not in df.columns: return None
    try: return int(df["index"].max()) + 1
    except Exception: return len(df)

# =========================
# 메인 제어부 (화면 전환용)
# =========================
st.title("📘 학생 생활습관 설문 및 DB 시스템")

# 세션 상태에 현재 화면 저장 (기본값은 설문지)
if "menu" not in st.session_state:
    st.session_state.menu = "📝 설문지 입력"

# 상단 메뉴 버튼 스타일의 라디오 선택바
menu = st.radio(
    "메뉴 선택", 
    ["📝 설문지 입력", "📊 설문 결과 및 DB"], 
    index=0 if st.session_state.menu == "📝 설문지 입력" else 1,
    horizontal=True
)
st.divider()

# 데이터 미리 로드
try:
    current_df = load_data()
except Exception as e:
    st.error("Supabase 데이터를 불러오지 못했습니다.")
    st.stop()

# =========================
# 화면 1: 설문지 입력
# =========================
if menu == "📝 설문지 입력":
    next_id = make_next_student_id(current_df)
    st.info(f"💡 다음에 생성될 자동 학생 ID : {next_id}")
    st.subheader("생활습관 설문 작성하기")

    with st.form("survey_form"):
        grade_class = st.selectbox("반", [f"1-{i}" for i in range(1, 11)])
        sleep_hours = st.number_input("수면시간 (시간)", min_value=0.0, max_value=24.0, value=6.0, step=0.5)
        phone_hours = st.number_input("스마트폰 사용시간 (시간)", min_value=0.0, max_value=24.0, value=3.0, step=0.5)
        breakfast = st.selectbox("아침식사 여부", ["YES", "NO"])
        commute_minutes = st.number_input("통학시간 (분)", min_value=0, max_value=180, value=30, step=5)
        
        st.markdown("### 피곤함 점수 (1:안피곤함 ~ 5:매우피곤함)")
        tired_score = st.radio("피곤함", [1, 2, 3, 4, 5], horizontal=True, label_visibility="collapsed")
        
        st.markdown("### 집중도 점수 (1:집중안됨 ~ 5:매우잘됨)")
        focus_score = st.radio("집중도", [1, 2, 3, 4, 5], horizontal=True, label_visibility="collapsed")
        
        favorite_subject = st.selectbox("좋아하는 과목", ["국어", "영어", "수학", "과학", "사회", "체육", "음악", "미술", "정보"])
        
        submitted = st.form_submit_button("💾 설문 제출하기")

    if submitted:
        latest_df = load_data()
        new_
