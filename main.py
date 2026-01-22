import random
from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd
import streamlit as st


# -----------------------------
# Config / Constants
# -----------------------------
DEFAULT_DATA_PATH = "youth_digital_wellbeing_apps_cleaned.csv"

NON_DIGITAL_ACTIVITY_POOL = [
    "10분 산책하기 🚶‍♀️",
    "물 한 컵 마시기 💧",
    "스트레칭 5분 🧘",
    "창밖 먼 곳 보기 2분 👀",
    "책 10페이지 읽기 📖",
    "방 정리 5분 🧹",
    "손글씨로 오늘 할 일 3개 적기 ✍️",
    "간단한 스케치/낙서 🎨",
    "가족/친구에게 짧게 안부 보내기 💬",
    "음악 듣고 눈 감기 5분 🎧",
    "가벼운 스쿼트 15회 🏋️",
    "간식 대신 과일/견과 챙기기 🍎",
]

EMOJI_BY_LEVEL = {
    "LOW": "🟢🙂",
    "MEDIUM": "🟡😯",
    "HIGH": "🔴😵‍💫",
}

LABEL_KO = {
    "LOW": "낮음",
    "MEDIUM": "주의",
    "HIGH": "위험",
}

LEVEL_DESC = {
    "LOW": "좋은 흐름이에요! 지금 패턴을 유지하면서 가끔 쉬어가면 더 좋아요.",
    "MEDIUM": "조금 과해질 수 있어요. 오늘은 '스위치 오프' 시간을 의도적으로 잡아보세요.",
    "HIGH": "과의존 위험이 꽤 높아요. 오늘은 강제 휴식(오프) 시간을 늘리고, 대체 활동을 꼭 붙여보는 걸 추천해요.",
}


# -----------------------------
# Data helpers (public benchmark)
# -----------------------------
def load_benchmark_df(uploaded_file) -> pd.DataFrame:
    """Load benchmark CSV. Tries utf-8-sig first, then cp949.
    Uses uploaded file if provided; otherwise tries DEFAULT_DATA_PATH in repo.
    """
    if uploaded_file is not None:
        raw = uploaded_file.read()
        # Try decoding in a robust way
        for enc in ["utf-8-sig", "utf-8", "cp949"]:
            try:
                return pd.read_csv(pd.io.common.BytesIO(raw), encoding=enc)
            except Exception:
                pass
        raise ValueError("업로드된 파일을 읽을 수 없습니다. 인코딩(utf-8/cp949)을 확인해주세요.")

    # Fallback: local file in repo
    for enc in ["utf-8-sig", "utf-8", "cp949"]:
        try:
            return pd.read_csv(DEFAULT_DATA_PATH, encoding=enc)
        except Exception:
            continue
    raise FileNotFoundError(
        f"기본 데이터 파일({DEFAULT_DATA_PATH})을 찾을 수 없어요. "
        "레포에 함께 업로드하거나, 사이드바에서 CSV를 업로드해주세요."
    )


def compute_prevalence_by_group(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Compute prevalence rates for each group:
    - internet_overdep_rate = (internet_risk + internet_caution)/internet_sample
    - phone_overdep_rate    = (phone_risk + phone_caution)/phone_sample
    - phone_risk_only_rate  = phone_risk/phone_sample (optional)
    Returns: {group: {"internet_rate":..., "phone_rate":...}}
    """
    required_cols = [
        "구분",
        "인터넷 과의존 현황_조사인원",
        "인터넷 과의존 현황_위험 사용자군",
        "인터넷 과의존 현황_주의 사용자군",
        "스마트폰 과의존 현황_조사 인원",
        "스마트폰 과의존 현황_위험 사용자군",
        "스마트폰 과의존 현황_주의 사용자군",
    ]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"데이터에 필요한 컬럼이 없어요: {c}")

    out: Dict[str, Dict[str, float]] = {}
    for _, r in df.iterrows():
        g = str(r["구분"]).strip()
        if g == "" or g.lower() == "nan":
            continue

        internet_sample = float(r["인터넷 과의존 현황_조사인원"])
        phone_sample = float(r["스마트폰 과의존 현황_조사 인원"])

        internet_risk = float(r["인터넷 과의존 현황_위험 사용자군"])
        internet_caution = float(r["인터넷 과의존 현황_주의 사용자군"])

        phone_risk = float(r["스마트폰 과의존 현황_위험 사용자군"])
        phone_caution = float(r["스마트폰 과의존 현황_주의 사용자군"])

        internet_rate = (internet_risk + internet_caution) / internet_sample if internet_sample > 0 else 0.0
        phone_rate = (phone_risk + phone_caution) / phone_sample if phone_sample > 0 else 0.0
        phone_risk_only = phone_risk / phone_sample if phone_sample > 0 else 0.0

        out[g] = {
            "internet_rate": internet_rate,
            "phone_rate": phone_rate,
            "phone_risk_only_rate": phone_risk_only,
        }
    return out


# -----------------------------
# Scoring / Recommendation logic
# -----------------------------
@dataclass
class DiagnosisResult:
    level: str
    score_0_100: int
    details: Dict[str, float]
    off_plan: Tuple[int, int]  # (on_minutes, off_minutes)


def minutes_to_base_score(total_minutes: int) -> float:
    """
    Base score from minutes.
    Simple, explainable mapping:
      <= 90m  -> low range
      90-180  -> medium range
      180-300 -> high-ish
      > 300   -> very high
    Returns 0~100.
    """
    if total_minutes <= 60:
        return 15
    if total_minutes <= 90:
        return 25
    if total_minutes <= 120:
        return 35
    if total_minutes <= 180:
        return 50
    if total_minutes <= 240:
        return 65
    if total_minutes <= 300:
        return 78
    if total_minutes <= 360:
        return 88
    return 95


def prevalence_multiplier(prevalence: float) -> float:
    """
    Convert prevalence rate (0~1) to a multiplier.
    If prevalence is higher, score increases slightly.
    Example: 0.10 -> ~1.00, 0.20 -> ~1.07, 0.30 -> ~1.14
    """
    # Clamp
    p = max(0.0, min(0.5, prevalence))
    return 1.0 + (p - 0.10) * 0.7  # tuned for gentle effect


def compute_off_plan(level: str, total_minutes: int) -> Tuple[int, int]:
    """
    Suggest 'digital switch off' plan.
    Returns (on, off) minutes per cycle.
    """
    if level == "LOW":
        return (120, 10)
    if level == "MEDIUM":
        return (90, 15)
    # HIGH
    # If extremely high minutes, push more off-time.
    if total_minutes >= 360:
        return (45, 20)
    return (60, 20)


def diagnose(
    grade_group: str,
    gender: str,
    internet_minutes: int,
    phone_minutes: int,
    benchmark_rates: Dict[str, Dict[str, float]],
) -> DiagnosisResult:
    total = max(0, internet_minutes) + max(0, phone_minutes)
    base = minutes_to_base_score(total)

    # Use benchmark prevalence (internet + phone) for selected group as context.
    grp = benchmark_rates.get(grade_group)
    if grp is None:
        # If group not found, use average across groups
        avg_internet = sum(v["internet_rate"] for v in benchmark_rates.values()) / max(1, len(benchmark_rates))
        avg_phone = sum(v["phone_rate"] for v in benchmark_rates.values()) / max(1, len(benchmark_rates))
        internet_rate, phone_rate = avg_internet, avg_phone
    else:
        internet_rate, phone_rate = grp["internet_rate"], grp["phone_rate"]

    # Gender adjustment (very light; because dataset here is aggregated and not minutes-based)
    gender_adj = 1.02 if gender == "여" else 1.00

    # Weighted multiplier
    mult = prevalence_multiplier((internet_rate + phone_rate) / 2.0) * gender_adj

    score = base * mult
    score = max(0.0, min(100.0, score))
    score_int = int(round(score))

    if score_int < 40:
        level = "LOW"
    elif score_int < 70:
        level = "MEDIUM"
    else:
        level = "HIGH"

    off_plan = compute_off_plan(level, total)

    details = {
        "total_minutes": float(total),
        "base_score": float(base),
        "internet_prevalence": float(internet_rate),
        "phone_prevalence": float(phone_rate),
        "multiplier": float(mult),
    }
    return DiagnosisResult(level=level, score_0_100=score_int, details=details, off_plan=off_plan)


def pick_activities(level: str) -> list:
    k = 3 if level == "LOW" else 4 if level == "MEDIUM" else 5
    return random.sample(NON_DIGITAL_ACTIVITY_POOL, k=min(k, len(NON_DIGITAL_ACTIVITY_POOL)))


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="청소년 디지털 웰빙 위험 진단", page_icon="📵", layout="centered")

st.title("📵 청소년 디지털 웰빙 위험 진단 (공공데이터 기반)")
st.caption("공공데이터(집계 통계)를 기준으로, 입력한 디지털 활동 시간을 바탕으로 위험 수준과 ‘스위치 오프’ 계획을 추천합니다.")

with st.sidebar:
    st.header("데이터(벤치마크)")
    uploaded = st.file_uploader("정제한 CSV 업로드(선택)", type=["csv"])
    st.caption("레포에 youth_digital_wellbeing_apps_cleaned.csv를 함께 올리면 업로드 없이도 동작해요.")

    st.divider()
    st.header("입력")
    grade_group = st.selectbox("학년/집단(구분)", ["초4", "중1", "고1"], index=1)
    gender = st.radio("성별", ["남", "여"], horizontal=True, index=0)

    internet_minutes = st.number_input("오늘 인터넷 사용 시간(분)", min_value=0, max_value=24 * 60, value=120, step=5)
    phone_minutes = st.number_input("오늘 스마트폰 사용 시간(분)", min_value=0, max_value=24 * 60, value=180, step=5)

    st.divider()
    run = st.button("🧪 위험 진단하기", use_container_width=True)

# Load benchmark
try:
    df_bench = load_benchmark_df(uploaded)
    bench_rates = compute_prevalence_by_group(df_bench)
except Exception as e:
    st.error(f"벤치마크 데이터를 불러오지 못했어요: {e}")
    st.stop()

# Show benchmark snapshot
with st.expander("📌 공공데이터(벤치마크) 요약 보기"):
    st.write("현재 로딩된 벤치마크 데이터(정제본) 미리보기:")
    st.dataframe(df_bench, use_container_width=True)

    st.write("구분별 (인터넷/스마트폰) 과의존(주의+위험) 비율:")
    rows = []
    for g, v in bench_rates.items():
        rows.append({
            "구분": g,
            "인터넷 과의존 비율(주의+위험)": round(v["internet_rate"] * 100, 2),
            "스마트폰 과의존 비율(주의+위험)": round(v["phone_rate"] * 100, 2),
            "스마트폰 위험군 비율(위험만)": round(v["phone_risk_only_rate"] * 100, 2),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

if run:
    result = diagnose(
        grade_group=grade_group,
        gender=gender,
        internet_minutes=int(internet_minutes),
        phone_minutes=int(phone_minutes),
        benchmark_rates=bench_rates,
    )

    emoji = EMOJI_BY_LEVEL[result.level]
    level_ko = LABEL_KO[result.level]

    st.subheader(f"{emoji} 진단 결과: **{level_ko}**")
    st.metric("위험 점수 (0~100)", result.score_0_100)

    st.write(LEVEL_DESC[result.level])

    total = int(result.details["total_minutes"])
    st.write(f"오늘 입력한 디지털 활동 총합: **{total}분**")

    # Switch-off plan
    on_m, off_m = result.off_plan
    st.subheader("⏱️ 디지털 스위치 오프(휴식) 추천")
    st.write(f"추천 루틴: **{on_m}분 사용 → {off_m}분 오프** 반복")
    st.info(
        f"예시) 지금부터 3시간 동안이라면: "
        f"`{on_m}분 사용 → {off_m}분 오프`를 2~3회 반복해보세요. 📵"
    )

    # Activities
    st.subheader("🌿 Non-digital activity 추천")
    picks = pick_activities(result.level)
    for a in picks:
        st.write(f"- {a}")

    # Gentle warning / cute message
    if result.level == "HIGH":
        st.warning("🔴 오늘은 ‘오프 시간’을 꼭 확보해보자! (폰아, 잠깐만 쉬자… 💤📵)")
    elif result.level == "MEDIUM":
        st.warning("🟡 조금만 조절하면 좋아져요! (5분만 쉬어도 효과가 커요 🙂)")
    else:
        st.success("🟢 아주 좋아요! (지금 리듬 유지 + 가벼운 휴식이면 완벽 ✨)")

    # Transparency
    with st.expander("🔎 점수 계산 방식(투명성)"):
        st.write(
            "- 이 앱은 **공공데이터(집계 통계)** 를 ‘벤치마크’로 사용합니다.\n"
            "- 개인별 정답 라벨(중독 진단 결과)이 있는 원자료가 아니라서, "
            "**‘설명 가능한 휴리스틱(규칙 기반)’** 으로 위험 점수를 산출합니다.\n"
            "- 추후 개인 설문/로그 데이터가 쌓이면 ML 모델로 고도화할 수 있어요."
        )
        st.json({
            "base_score_from_minutes": result.details["base_score"],
            "benchmark_internet_prevalence": result.details["internet_prevalence"],
            "benchmark_phone_prevalence": result.details["phone_prevalence"],
            "multiplier": result.details["multiplier"],
            "final_score_0_100": result.score_0_100,
        })

else:
    st.info("왼쪽 사이드바에서 값을 입력하고 **위험 진단하기** 버튼을 눌러주세요 🙂")
