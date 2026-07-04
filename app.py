import re
import pandas as pd
import streamlit as st
from supabase import create_client

# =========================
# 페이지 설정
# =========================
st.set_page_config(
    page_title="학생 생활습관 설문 데이터베이스",
    page_icon="📘",
    layout="centered"
)

# =========================
# 디자인 설정 (CSS)
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# 메인 제목
# =========================
st.title("📘 학생 생활습관 설문 및 DB 시스템")
st.write("설문을 입력하고 제출하면 Supabase 데이터베이스에 실시간으로 기록되고 아래 대시보드에 반영됩니다.")
st.divider()

# =========================
# 현재 데이터 미리 로드
# =========================
try:
    current_df = load_data()
except Exception as e:
    st.error("Supabase 데이터를 불러오지 못했습니다.")
    st.write("확인할 것: Supabase 프로젝트 상태, RLS 설정, URL, KEY, 테이블 이름")
    st.write(e)
    st.stop()

next_id = make_next_student_id(current_df)
st.info(f"💡 다음에 생성될 자동 학생 ID : {next_id}")

# =========================
# 1. 입력 폼 섹션
# =========================
st.subheader("📝 1. 설문 입력하기")

with st.form("survey_form"):
    grade_class = st.selectbox(
        "반",
        [f"1-{i}" for i in range(1, 11)]
    )

    sleep_hours = st.number_input(
        "수면시간 (시간 단위)",
        min_value=0.0,
        max_value=24.0,
        value=6.0,
        step=0.5
    )

    phone_hours = st.number_input(
        "스마트폰 사용시간 (시간 단위)",
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
        "통학시간 (분)",
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
        ["국어", "영어", "수학", "과학", "사회", "체육", "음악", "미술", "정보"]
    )

    submitted = st.form_submit_button("💾 설문 제출하기")

# =========================
# 데이터 저장 로직
# =========================
if submitted:
    latest_df = load_data()
    new_student_id = make_next_student_id(latest_df)
    new_index = make_next_index(latest_df)

    # 안전하게 정수(int)형으로 변환하여 데이터 구성 (bigint 에러 방지)
    data = {
        "student_id": new_student_id,
        "grade_class": grade_class,
        "sleep_hours": int(sleep_hours),
        "phone_hours": int(phone_hours),
        "breakfast": breakfast,
        "commute_minutes": int(commute_minutes),
        "tired_score": int(tired_score),
        "focus_score": int(focus_score),
        "favorite_subject": favorite_subject
    }

    if new_index is not None:
        data["index"] = new_index

    try:
        supabase.table(TABLE_NAME).insert(data).execute()
        st.success(f"🎉 성공적으로 데이터베이스에 저장되었습니다! (학생 ID : {new_student_id})")
        st.balloons()
        st.rerun()
    except Exception as e:
        st.error("저장 중 오류가 발생했습니다.")
        st.write("확인할 것: Supabase RLS 설정, 컬럼 이름 불일치 여부")
        st.write(e)

# =========================
# 2. 실시간 데이터베이스 확인 및 통계 섹션
# =========================
st.divider()
st.subheader("📊 2. 전체 설문 데이터베이스 실시간 조회")

try:
    df = load_data()

    if df.empty:
        st.info("아직 데이터베이스에 저장된 데이터가 없습니다.")
    else:
        # 최신 등록된 학생 데이터가 맨 위로 오도록 역순 정렬
        if "student_id" in df.columns:
            df = df.sort_values(by="student_id", ascending=False)

        # 보기 편하게 정돈된 컬럼 순서 설정
        display_columns = [
            "student_id", "grade_class", "sleep_hours", "phone_hours", 
            "breakfast", "commute_minutes", "tired_score", "focus_score", "favorite_subject"
        ]
        available_cols = [col for col in display_columns if col in df.columns]
        df_to_show = df[available_cols]

        # 엑셀 스타일의 인터랙티브 데이터 테이블 렌더링
        st.dataframe(
            df_to_show,
            use_container_width=True,
            height=350
        )
        st.success(f"🔥 현재 데이터베이스에 총 {len(df)}개의 설문 데이터가 누적되어 있습니다.")

        # -------------------------
        # 실시간 간단 통계 시각화
        # -------------------------
        st.markdown("### 📈 데이터베이스 실시간 분석")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 👑 좋아하는 과목 순위")
            if "favorite_subject" in df.columns:
                subject_counts = df["favorite_subject"].value_counts()
                st.bar_chart(subject_counts)

        with col2:
            st.markdown("##### 🕒 수면 및 스마트폰 평균")
            if "sleep_hours" in df.columns and "phone_hours" in df.columns:
                avg_sleep = df["sleep_hours"].mean()
                avg_phone = df["phone_hours"].mean()
                
                st.metric(label="📊 평균 수면 시간", value=f"{avg_sleep:.1f} 시간")
                st.metric(label="📱 평균 스마트폰 사용 시간", value=f"{avg_phone:.1f} 시간")

except Exception as e:
    st.error("데이터베이스를 조회하는 중 오류가 발생했습니다.")
    st.write(e)
