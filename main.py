import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="청소년 디지털 밸런스", page_icon="📱", layout="centered")

# Load data
df_view = pd.read_csv("online viewing.csv", encoding="utf-8-sig")
df_usage = pd.read_csv("daily_usage.csv", encoding="utf-8-sig")

st.title("📵 청소년 디지털 밸런스 코치")
st.caption("공공데이터 기반 + 나의 기록으로 디지털 습관을 관리해요")

st.header("👤 내 정보")
age = st.number_input("나이", 10, 19, 15)
gender = st.radio("성별", ["남", "여"], horizontal=True)

st.header("📊 오늘의 디지털 활동")
total_time = st.slider("오늘 스마트폰 총 사용 시간 (분)", 0, 720, 240, step=10)
video_time = st.slider("오늘 영상 시청 시간 (분)", 0, total_time, 120, step=10)

if st.button("오늘의 디지털 진단"):
    st.divider()

    # Risk 판단
    if video_time < 60:
        level = "🟢 안전"
        msg = "아주 좋아요! 지금 패턴을 유지하세요 😊"
        off = "10분 휴식"
    elif video_time < 120:
        level = "🟡 주의"
        msg = "조금 줄이면 더 좋아요 🙂"
        off = "20분 OFF"
    else:
        level = "🔴 위험"
        msg = "오늘은 사용량이 많아요 😵‍💫"
        off = "30분 OFF"

    st.subheader(f"오늘 상태: {level}")
    st.write(msg)

    # 비교 시각화
    avg = 195  # 청소년 평균 (통계 기반 가상값, 실제 데이터 연결 가능)

    st.write("### 📈 또래 평균과 비교")
    st.bar_chart({
        "나": total_time,
        "또래 평균": avg
    })

    diff = total_time - avg
    if diff > 0:
        st.warning(f"평균보다 {diff}분 더 사용했어요 ⚠️")
    else:
        st.success("평균보다 적게 사용했어요 👍")

    # 행동 코칭
    st.write("### 🎯 오늘의 디지털 코칭")
    st.info(f"✔ 스마트폰 {off}")
    st.info("✔ 산책 10분 🚶")
    st.info("✔ 눈 휴식 5분 👀")
    st.info("✔ 스트레칭 5분 🧘")

    st.balloons()
