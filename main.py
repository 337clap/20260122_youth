import os
import random
from datetime import datetime, date, timedelta
from typing import Dict, Tuple

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt


# -----------------------------
# Files
# -----------------------------
BENCH_DEFAULT_PATH = "youth_digital_wellbeing_apps_cleaned.csv"
LOG_DEFAULT_PATH = "user_activity_log.csv"


# -----------------------------
# Content
# -----------------------------
EMOJI_BY_LEVEL = {"LOW": "🟢🙂", "MEDIUM": "🟡😯", "HIGH": "🔴😵‍💫"}
LABEL_KO = {"LOW": "낮음", "MEDIUM": "주의", "HIGH": "위험"}

LEVEL_COPY = {
    "LOW": "좋은 흐름이에요! 유지하면서 ‘짧은 오프’만 습관화하면 더 좋아요.",
    "MEDIUM": "조절이 필요해요. 오늘은 오프 시간을 ‘일정’처럼 확정해보세요.",
    "HIGH": "과의존 위험이 높아요. 오늘은 ‘강제 오프’ + 대체 활동을 꼭 붙여요.",
}

NON_DIGITAL_ACTIVITY_POOL = [
    "산책 10분 🚶",
    "스트레칭 5분 🧘",
    "물 한 컵 💧",
    "책 10페이지 📖",
    "눈 쉬기 2분(먼 곳 보기) 👀",
    "방 정리 5분 🧹",
    "손글씨로 감정 한 줄 ✍️",
    "가벼운 스쿼트 15회 🏋️",
    "음악 듣고 눈 감기 5분 🎧",
    "간식 대신 과일 🍎",
    "친구/가족 안부 문자 💬",
]

DIGITAL_SWITCH_MESSAGES = {
    "LOW": "오늘도 잘하고 있어요! 📵✨",
    "MEDIUM": "5~15분만 쉬어도 효과 커요 🙂📵",
    "HIGH": "지금은 ‘오프’가 진짜 도움돼요… 💤📵",
}


# -----------------------------
# Benchmark (public data)
# -----------------------------
def load_csv_robust(path_or_bytes) -> pd.DataFrame:
    # Accept path or bytes
    encodings = ["utf-8-sig", "utf-8", "cp949"]
    if isinstance(path_or_bytes, (bytes, bytearray)):
        for enc in encodings:
            try:
                return pd.read_csv(pd.io.common.BytesIO(path_or_bytes), encoding=enc)
            except Exception:
                pass
        raise ValueError("CSV 인코딩을 읽지 못했어요. utf-8/cp949를 확인해주세요.")
    else:
        for enc in encodings:
            try:
                return pd.read_csv(path_or_bytes, encoding=enc)
            except Exception:
                pass
        raise FileNotFoundError(f"벤치마크 CSV를 찾을 수 없어요: {path_or_bytes}")


def load_benchmark_df(uploaded) -> pd.DataFrame:
    if uploaded is not None:
        return load_csv_robust(uploaded.read())
    return load_csv_robust(BENCH_DEFAULT_PATH)


def compute_rates(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    required = [
        "구분",
        "인터넷 과의존 현황_조사인원",
        "인터넷 과의존 현황_위험 사용자군",
        "인터넷 과의존 현황_주의 사용자군",
        "스마트폰 과의존 현황_조사 인원",
        "스마트폰 과의존 현황_위험 사용자군",
        "스마트폰 과의존 현황_주의 사용자군",
    ]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"벤치마크 데이터 컬럼 누락: {c}")

    out = {}
    for _, r in df.iterrows():
        g = str(r["구분"]).strip()
        if g == "" or g.lower() == "nan":
            continue

        internet_n = float(r["인터넷 과의존 현황_조사인원"])
        phone_n = float(r["스마트폰 과의존 현황_조사 인원"])

        internet_risk = float(r["인터넷 과의존 현황_위험 사용자군"])
        internet_caution = float(r["인터넷 과의존 현황_주의 사용자군"])

        phone_risk = float(r["스마트폰 과의존 현황_위험 사용자군"])
        phone_caution = float(r["스마트폰 과의존 현황_주의 사용자군"])

        internet_rate = (internet_risk + internet_caution) / internet_n if internet_n > 0 else 0.0
        phone_rate = (phone_risk + phone_caution) / phone_n if phone_n > 0 else 0.0

        out[g] = {"internet_rate": internet_rate, "phone_rate": phone_rate}
    return out


# -----------------------------
# Personal Log (in-app data)
# -----------------------------
LOG_COLUMNS = [
    "date",            # YYYY-MM-DD
    "group",           # 초4/중1/고1 or user-selected
    "gender",          # 남/여
    "internet_min",    # int
    "phone_min",       # int
    "sleep_hours",     # float (optional)
    "stress_1_10",     # int (optional)
    "mood_1_10",       # int (optional)
    "note",            # str (optional)
]


def empty_log_df() -> pd.DataFrame:
    return pd.DataFrame(columns=LOG_COLUMNS)


def load_log_df(uploaded_log) -> pd.DataFrame:
    # priority: uploaded > local file > empty
    if uploaded_log is not None:
        df = load_csv_robust(uploaded_log.read())
        return normalize_log_df(df)
    if os.path.exists(LOG_DEFAULT_PATH):
        try:
            df = load_csv_robust(LOG_DEFAULT_PATH)
            return normalize_log_df(df)
        except Exception:
            return empty_log_df()
    return empty_log_df()


def normalize_log_df(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure all needed columns exist
    for c in LOG_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df = df[LOG_COLUMNS].copy()

    # Types
    df["date"] = df["date"].astype(str)
    for c in ["internet_min", "phone_min"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["sleep_hours"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["stress_1_10", "mood_1_10"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop obviously bad dates
    df = df[df["date"].str.len() >= 8]
    return df


def safe_save_log(df: pd.DataFrame) -> bool:
    # Streamlit Cloud는 파일 저장이 휘발될 수 있어도,
    # 세션 중에는 저장이 되곤 합니다. 실패하면 다운로드로 대체.
    try:
        df.to_csv(LOG_DEFAULT_PATH, index=False, encoding="utf-8-sig")
        return True
    except Exception:
        return False


# -----------------------------
# Diagnosis logic (experience-first)
# -----------------------------
def base_score_from_minutes(total_min: int) -> float:
    # explainable piecewise mapping 0~100
    if total_min <= 60: return 15
    if total_min <= 90: return 25
    if total_min <= 120: return 35
    if total_min <= 180: return 50
    if total_min <= 240: return 65
    if total_min <= 300: return 78
    if total_min <= 360: return 88
    return 95


def benchmark_context_multiplier(group: str, gender: str, rates: Dict[str, Dict[str, float]]) -> float:
    # Gentle adjustment from benchmark prevalence (context only)
    if group in rates:
        p = (rates[group]["internet_rate"] + rates[group]["phone_rate"]) / 2.0
    else:
        p = np.mean([(v["internet_rate"] + v["phone_rate"]) / 2.0 for v in rates.values()]) if rates else 0.15

    p = float(np.clip(p, 0.05, 0.40))
    mult = 1.0 + (p - 0.10) * 0.7
    if gender == "여":
        mult *= 1.02  # tiny
    return float(np.clip(mult, 0.9, 1.2))


def decide_level(score: int) -> str:
    if score < 40: return "LOW"
    if score < 70: return "MEDIUM"
    return "HIGH"


def switch_off_plan(level: str, total_min: int) -> Tuple[int, int]:
    if level == "LOW":
        return (120, 10)
    if level == "MEDIUM":
        return (90, 15)
    # HIGH
    if total_min >= 360:
        return (45, 20)
    return (60, 20)


def recommend_activities(level: str) -> list:
    k = 3 if level == "LOW" else 4 if level == "MEDIUM" else 5
    return random.sample(NON_DIGITAL_ACTIVITY_POOL, k=min(k, len(NON_DIGITAL_ACTIVITY_POOL)))


def recommend_off_window(level: str, preferred_start_hour: int, preferred_end_hour: int) -> str:
    # Suggest a realistic "off block" in evening by default
    if level == "LOW":
        minutes = 15
    elif level == "MEDIUM":
        minutes = 30
    else:
        minutes = 45

    # Keep within window
    start = preferred_start_hour
    end = preferred_end_hour
    if end <= start:
        end = start + 2  # fallback

    # Put it near the end (before sleep)
    off_start = max(start, end - 2)
    off_end = min(end, off_start + 1)

    # Convert to times
    return f"{off_start:02d}:00 ~ {off_end:02d}:00 사이에 **{minutes}분 오프 블록** 추천"


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Digital Balance (공공데이터+내 로그)", page_icon="📵", layout="centered")
st.title("📵 Digital Balance")
st.caption("공공데이터(벤치마크) + 내 기록(로그)로 ‘진짜 데이터 기반’ 디지털 웰빙 앱을 만듭니다.")

with st.sidebar:
    st.header("1) 벤치마크 데이터")
    bench_upload = st.file_uploader("youth_digital_wellbeing_apps_cleaned.csv 업로드(선택)", type=["csv"])
    st.caption("레포에 같은 파일을 올려두면 업로드 없이 자동 로딩됩니다.")

    st.divider()
    st.header("2) 내 로그 데이터")
    log_upload = st.file_uploader("기존 로그 업로드(선택)", type=["csv"])
    st.caption("Streamlit Cloud는 저장이 휘발될 수 있어요. 로그는 내려받아 보관하는 걸 추천해요.")

# Load data
try:
    bench_df = load_benchmark_df(bench_upload)
    bench_rates = compute_rates(bench_df)
except Exception as e:
    st.error(f"벤치마크 로딩 실패: {e}")
    st.stop()

log_df = load_log_df(log_upload)

tabs = st.tabs(["🧪 오늘 진단", "📈 추세", "🗓️ 주간 리포트", "⚙️ 데이터"])

# -----------------------------
# Tab 1: Today diagnosis + add log
# -----------------------------
with tabs[0]:
    st.subheader("🧪 오늘의 위험 진단 & 기록")
    col1, col2 = st.columns(2)

    with col1:
        group = st.selectbox("학년/집단(구분)", ["초4", "중1", "고1"], index=1)
        gender = st.radio("성별", ["남", "여"], horizontal=True)
        the_date = st.date_input("날짜", value=date.today())

    with col2:
        internet_min = st.number_input("인터넷 사용(분)", min_value=0, max_value=24*60, value=120, step=5)
        phone_min = st.number_input("스마트폰 사용(분)", min_value=0, max_value=24*60, value=180, step=5)

    st.markdown("**(선택) 컨디션 입력** — 정확한 예측 모델은 아니지만, ‘내 변화’를 기록하는 데 도움이 돼요.")
    c1, c2, c3 = st.columns(3)
    with c1:
        sleep_hours = st.number_input("수면시간(시간)", min_value=0.0, max_value=16.0, value=7.0, step=0.5)
    with c2:
        stress = st.number_input("스트레스(1~10)", min_value=1, max_value=10, value=5, step=1)
    with c3:
        mood = st.number_input("기분(1~10)", min_value=1, max_value=10, value=6, step=1)

    note = st.text_input("메모(선택)", placeholder="예: 시험기간이라 유튜브 많이 봄…")

    # Diagnose
    total = int(internet_min) + int(phone_min)
    base = base_score_from_minutes(total)
    mult = benchmark_context_multiplier(group, gender, bench_rates)

    # Light well-being adjustment using self inputs (log-driven UX)
    # (This makes the app feel responsive to the user’s data)
    adj = 1.0
    if sleep_hours < 6:
        adj *= 1.05
    if stress >= 8:
        adj *= 1.05
    if mood <= 3:
        adj *= 1.03

    score = int(round(np.clip(base * mult * adj, 0, 100)))
    level = decide_level(score)
    emoji = EMOJI_BY_LEVEL[level]

    st.divider()
    st.subheader(f"{emoji} 진단 결과: **{LABEL_KO[level]}**")
    st.metric("위험 점수 (0~100)", score)
    st.write(LEVEL_COPY[level])
    st.write(f"오늘 디지털 활동 총합: **{total}분**")

    on_m, off_m = switch_off_plan(level, total)
    st.subheader("⏱️ 디지털 스위치 오프 추천")
    st.write(f"추천 루틴: **{on_m}분 사용 → {off_m}분 오프** 반복")
    st.info(DIGITAL_SWITCH_MESSAGES[level])

    # Off window suggestion
    st.subheader("🕒 오늘 오프(OFF) 블록 제안")
    start_h = st.slider("오프 가능한 시작 시각(시)", 0, 23, 20)
    end_h = st.slider("오프 가능한 끝 시각(시)", 0, 23, 23)
    st.write(recommend_off_window(level, start_h, end_h))

    st.subheader("🌿 Non-digital activity 추천")
    for a in recommend_activities(level):
        st.write(f"- {a}")

    # Save log
    st.divider()
    if st.button("💾 오늘 기록 저장", use_container_width=True):
        new_row = {
            "date": the_date.isoformat(),
            "group": group,
            "gender": gender,
            "internet_min": int(internet_min),
            "phone_min": int(phone_min),
            "sleep_hours": float(sleep_hours),
            "stress_1_10": int(stress),
            "mood_1_10": int(mood),
            "note": note,
        }
        log_df2 = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
        log_df2 = normalize_log_df(log_df2)

        # Drop duplicates on same date (keep latest)
        log_df2 = log_df2.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
        log_df = log_df2  # update in this run

        saved = safe_save_log(log_df2)
        if saved:
            st.success("저장 완료! (단, Streamlit Cloud는 저장이 휘발될 수 있어요. 아래에서 로그 다운로드도 해두세요.)")
        else:
            st.warning("서버 저장에 실패했어요. 아래에서 로그를 다운로드해 보관해주세요.")

        st.download_button(
            "⬇️ 내 로그 CSV 다운로드",
            data=log_df2.to_csv(index=False, encoding="utf-8-sig"),
            file_name=LOG_DEFAULT_PATH,
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("🔎 점수 계산(투명성)"):
        # Show benchmark prevalence for chosen group
        p_i = bench_rates.get(group, {}).get("internet_rate", np.nan)
        p_p = bench_rates.get(group, {}).get("phone_rate", np.nan)
        st.json({
            "total_minutes": total,
            "base_score_from_minutes": base,
            "benchmark_internet_overdep_rate": p_i,
            "benchmark_phone_overdep_rate": p_p,
            "benchmark_multiplier": mult,
            "sleep/stress/mood_adjustment": adj,
            "final_score_0_100": score,
        })


# -----------------------------
# Tab 2: Trend
# -----------------------------
with tabs[1]:
    st.subheader("📈 내 추세 (내 데이터가 쌓일수록 똑똑해짐)")
    if len(log_df) == 0:
        st.info("아직 저장된 로그가 없어요. ‘오늘 진단’에서 기록을 저장해보세요 🙂")
    else:
        df = log_df.copy()
        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date_dt"]).sort_values("date_dt")
        df["total_min"] = df["internet_min"].fillna(0) + df["phone_min"].fillna(0)

        # Rolling averages
        df["total_7d_avg"] = df["total_min"].rolling(7, min_periods=1).mean()
        df["total_14d_avg"] = df["total_min"].rolling(14, min_periods=1).mean()

        st.write("최근 기록:")
        st.dataframe(df[["date", "group", "gender", "internet_min", "phone_min", "total_min", "sleep_hours", "stress_1_10", "mood_1_10", "note"]].tail(14), use_container_width=True)

        st.divider()
        st.write("총 디지털 시간 추세(분)")

        plt.figure()
        plt.plot(df["date_dt"], df["total_min"], marker="o", label="Total (min)")
        plt.plot(df["date_dt"], df["total_7d_avg"], marker="o", label="7-day avg")
        plt.plot(df["date_dt"], df["total_14d_avg"], marker="o", label="14-day avg")
        plt.xlabel("Date")
        plt.ylabel("Minutes")
        plt.legend()
        st.pyplot(plt.gcf(), clear_figure=True)

        st.write("인터넷/스마트폰 분리 추세(분)")
        plt.figure()
        plt.plot(df["date_dt"], df["internet_min"], marker="o", label="Internet")
        plt.plot(df["date_dt"], df["phone_min"], marker="o", label="Phone")
        plt.xlabel("Date")
        plt.ylabel("Minutes")
        plt.legend()
        st.pyplot(plt.gcf(), clear_figure=True)

        # Simple insights
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else None
        if prev is not None:
            delta = int(last["total_min"] - prev["total_min"])
            arrow = "⬆️" if delta > 0 else "⬇️" if delta < 0 else "➡️"
            st.info(f"전일 대비 총 디지털 시간: **{arrow} {delta}분**")


# -----------------------------
# Tab 3: Weekly report
# -----------------------------
with tabs[2]:
    st.subheader("🗓️ 주간 리포트")
    if len(log_df) == 0:
        st.info("로그가 있어야 주간 리포트가 나와요. 먼저 ‘오늘 진단’에서 기록을 저장해주세요 🙂")
    else:
        df = log_df.copy()
        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date_dt"]).sort_values("date_dt")
        df["total_min"] = df["internet_min"].fillna(0) + df["phone_min"].fillna(0)

        end = df["date_dt"].max()
        start = end - timedelta(days=6)
        week = df[(df["date_dt"] >= start) & (df["date_dt"] <= end)].copy()

        st.write(f"기간: **{start.date()} ~ {end.date()}**")

        total_sum = int(week["total_min"].sum())
        avg = float(week["total_min"].mean()) if len(week) else 0.0
        max_day = week.loc[week["total_min"].idxmax()] if len(week) else None

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("주간 총합(분)", total_sum)
        with c2:
            st.metric("일 평균(분)", int(round(avg)))
        with c3:
            if max_day is not None:
                st.metric("최대 사용일", f"{max_day['date']} ({int(max_day['total_min'])}분)")
            else:
                st.metric("최대 사용일", "-")

        st.divider()
        st.write("주간 총 디지털 시간(분)")
        plt.figure()
        plt.plot(week["date_dt"], week["total_min"], marker="o")
        plt.xlabel("Date")
        plt.ylabel("Minutes")
        st.pyplot(plt.gcf(), clear_figure=True)

        # Personalized recommendations based on weekly pattern
        st.subheader("✅ 다음 주 액션 플랜")
        avg_min = avg
        if avg_min >= 360:
            target = int(round(avg_min * 0.8))
            st.write(f"- 다음 주 목표: **일 평균 {target}분 이하** (이번 주 대비 약 20% 줄이기)")
            st.write("- ‘45분 사용 → 20분 오프’ 루틴을 저녁 시간에 2회 적용해보세요.")
        elif avg_min >= 240:
            target = int(round(avg_min * 0.85))
            st.write(f"- 다음 주 목표: **일 평균 {target}분 이하** (약 15% 줄이기)")
            st.write("- ‘60분 사용 → 20분 오프’ 루틴을 하루 2회 적용해보세요.")
        elif avg_min >= 180:
            target = int(round(avg_min * 0.9))
            st.write(f"- 다음 주 목표: **일 평균 {target}분 이하** (약 10% 줄이기)")
            st.write("- ‘90분 사용 → 15분 오프’ 루틴을 하루 1~2회 적용해보세요.")
        else:
            st.write("- 다음 주 목표: **현재 수준 유지 + 오프 습관 유지**")
            st.write("- ‘120분 사용 → 10분 오프’를 유지해보세요.")

        st.write("- 추천 대체 활동(상위 3개):")
        for a in random.sample(NON_DIGITAL_ACTIVITY_POOL, 3):
            st.write(f"  - {a}")


# -----------------------------
# Tab 4: Data admin
# -----------------------------
with tabs[3]:
    st.subheader("⚙️ 데이터 확인 & 내보내기")

    with st.expander("벤치마크(공공데이터) 미리보기"):
        st.dataframe(bench_df, use_container_width=True)
        # rates table
        rows = []
        for g, v in bench_rates.items():
            rows.append({
                "구분": g,
                "인터넷 과의존 비율(주의+위험) %": round(v["internet_rate"] * 100, 2),
                "스마트폰 과의존 비율(주의+위험) %": round(v["phone_rate"] * 100, 2),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.divider()
    st.write("내 로그 데이터")
    if len(log_df) == 0:
        st.info("저장된 로그가 없습니다.")
    else:
        st.dataframe(log_df, use_container_width=True)

    st.download_button(
        "⬇️ 내 로그 CSV 다운로드",
        data=log_df.to_csv(index=False, encoding="utf-8-sig") if len(log_df) else empty_log_df().to_csv(index=False, encoding="utf-8-sig"),
        file_name=LOG_DEFAULT_PATH,
        mime="text/csv",
        use_container_width=True,
    )

    st.caption("팁: Streamlit Cloud는 서버 저장이 초기화될 수 있으니, 로그 CSV는 주기적으로 다운로드해 보관하세요.")
