import re
import pandas as pd
import streamlit as st
from supabase import create_client

# =========================
# 페이지 설정
# =========================

st.set_page_config(
    page_title="학생 생활습관 설문",
    page_icon="📘",
    layout="centered"
)

# =========================
# 디자인 설정
# =========================

st.markdown("""
<style>

.block-container {
    max-width: 900px;
    padding-top: 2rem;
}

h1 {
    text-align: center;
    color: #1f2937;
    font-weight: 800;
}

h2, h3 {
    color: #374151;
}

.stForm {
    background-color: white;
    padding: 30px;
    border-radius: 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.stButton button {
    width: 100%;
    border-radius: 12px;
    font-size: 18px;
    font-weight: bold;
    padding: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# Supabase 연결 정보
# =========================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    TABLE_NAME = st.secrets.get("TABLE_NAME", "student_survey")
except Exception:
    st.error("Streamlit Secrets에 SUPABASE_URL, SUPABASE_KEY, TABLE_NAME을 입력해야 합니다.")
    st.stop()

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# =========================
# 데이터 불러오기 함수
# =========================

def load_data():
    response = (
        supabase
        .table(TABLE_NAME)
        .select("*")
        .execute()
    )
    return pd.DataFrame(response.data)

# =========================
# 학생 ID 자동 생성 함수
# =========================

def make_next_student_id(df):
    if df.empty or "student_id" not in df.columns:
        return "S001"

    max_number = 0

    for sid in df["student_id"].dropna():
        match = re.search(r"\d+", str(sid))

        if match:
            number = int(match.group())

            if number > max_number:
                max_number = number

    return f"S{max_number + 1:03d}"

# =========================
# index 자동 생성 함수
# =========================

def make_next_index(df):
    if df.empty or "index" not in df.columns:
        return None

    try:
        return int(df["index"].max()) + 1
    except Exception:
        return len(df)

# =========================
# 제목
# =========================

st.title("📘 학생 생활습관 설문 웹앱")

st.write(
    "설문을 입력하고 제출하면 Supabase 데이터베이스에 자동으로 저장됩니다."
)

st.divider()

# =========================
# 현재 데이터 확인
# =========================

try:
    current_df = load_data()
except Exception as e:
    st.error("Supabase 데이터를 불러오지 못했습니다.")
    st.write("확인할 것: Supabase 프로젝트 상태, RLS 설정, URL, KEY, 테이블 이름")
    st.write(e)
    st.stop()

next_id = make_next_student_id(current_df)

st.info(f"자동 생성 학생 ID : {next_id}")

# =========================
# 입력 폼
# =========================

st.subheader("1. 설문 입력하기")

with st.form("survey_form"):

    grade_class = st.selectbox(
        "반",
        [
            "1-1",
            "1-2",
            "1-3",
            "1-4",
            "1-5",
            "1-6",
            "1-7",
            "1-8",
            "1-9",
            "1-10"
        ]
    )

    sleep_hours = st.number_input(
        "수면시간",
        min_value=0.0,
        max_value=24.0,
        value=6.0,
        step=0.5
    )

    phone_hours = st.number_input(
        "스마트폰 사용시간",
        min_value=0.0,
        max_value=24.0,
        value=3.0,
        step=0.5
    )

    breakfast = st.selectbox(
        "아침식사 여부",
        ["YES", "NO"]
    )

    commute_minutes = st.number_input(
        "통학시간(분)",
        min_value=0,
        max_value=180,
        value=30,
        step=5
    )

    st.markdown("### 피곤함 점수")
    st.caption("1 = 전혀 피곤하지 않음, 5 = 매우 피곤함")

    tired_score = st.radio(
        "피곤함 점수 선택",
        [1, 2, 3, 4, 5],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("### 집중도 점수")
    st.caption("1 = 집중이 잘 안 됨, 5 = 매우 잘 집중됨")

    focus_score = st.radio(
        "집중도 점수 선택",
        [1, 2, 3, 4, 5],
        horizontal=True,
        label_visibility="collapsed"
    )

    favorite_subject = st.selectbox(
        "좋아하는 과목",
        [
            "국어",
            "영어",
            "수학",
            "과학",
            "사회",
            "체육",
            "음악",
            "미술",
            "정보"
        ]
    )

    submitted = st.form_submit_button(
        "💾 설문 제출하기"
    )

# =========================
# 데이터 저장
# =========================

if submitted:

    latest_df = load_data()
    new_student_id = make_next_student_id(latest_df)
    new_index = make_next_index(latest_df)

    data = {
        "student_id": new_student_id,
        "grade_class": grade_class,
        "sleep_hours": sleep_hours,
        "phone_hours": phone_hours,
        "breakfast": breakfast,
        "commute_minutes": commute_minutes,
        "tired_score": tired_score,
        "focus_score": focus_score,
        "favorite_subject": favorite_subject
    }

    if new_index is not None:
        data["index"] = new_index

    try:
        supabase.table(TABLE_NAME).insert(data).execute()

        st.success(f"설문이 저장되었습니다. 학생 ID : {new_student_id}")
        st.balloons()
        st.rerun()

    except Exception as e:
        st.error("저장 중 오류가 발생했습니다.")
        st.write("확인할 것: RLS 설정, 테이블 이름, 컬럼 이름, Primary Key 중복 여부")
        st.write(e)

# =========================
# 저장된 데이터 확인
# =========================

st.divider()

st.subheader("2. 저장된 설문 데이터 확인")

try:
    df = load_data()

    if df.empty:
        st.info("아직 저장된 데이터가 없습니다.")
    else:
        if "student_id" in df.columns:
            df = df.sort_values(by="student_id")

        st.dataframe(
            df,
            use_container_width=True
        )

        st.success(f"총 데이터 수 : {len(df)}개")

except Exception as e:
    st.error("데이터 조회 중 오류가 발생했습니다.")
    st.write(e)
