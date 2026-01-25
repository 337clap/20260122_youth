import os
from datetime import date
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================
# 🔥 0) 필수 파일(공공데이터 벤치마크) — 선택 아님!
# =====================================================
REQUIRED_BENCH_FILES = ["online viewing.csv", "daily_usage.csv"]

# =====================================================
# 🔥 1) 브랜딩(여기 바꾸면 제목/문구 전체 변경)
# =====================================================
APP_NAME = "DIGI BALANCE"
TAGLINE_1 = "나를 위한 스마트한 디지털 습관"
TAGLINE_2 = "오늘 기록하고, 내 패턴을 예쁘게 확인해요 ✨"

st.set_page_config(page_title=APP_NAME, page_icon="🌱", layout="centered")

# =====================================================
# 🔥 2) Z세대 톤 CSS (카드/필/간격)
# =====================================================
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 980px;}
      h1, h2, h3 {letter-spacing: -0.6px;}
      .subtle {color:#8b8b8b;}
      .card {
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 18px;
        padding: 18px 18px;
        background: rgba(250,250,250,0.86);
        margin-bottom: 14px;
      }
      .pill {
        display:inline-block; padding:6px 10px; border-radius:999px;
        background: rgba(0,0,0,0.05); margin-right:6px; font-size: 0.9rem;
      }
      .big {font-size: 1.25rem; font-weight: 800;}
      .muted {color:#6f6f6f;}
      .good {color:#138a3d; font-weight:800;}
      .warn {color:#c77b00; font-weight:800;}
      .bad  {color:#c0362c; font-weight:800;}
      .center {text-align:center;}
      .tiny {font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 🔥 3) 헤더(“공공데이터 기반” 문구 제거 완료)
# =====================================================
st.markdown(
    f"""
    <div class="card">
      <div style="display:flex; align-items:center; gap:14px;">
        <div style="font-size:40px;">🌱</div>
        <div>
          <div style="font-size:44px; font-weight:900; line-height:1;">{APP_NAME}</div>
          <div class="big" style="margin-top:10px;">{TAGLINE_1}</div>
          <div class="subtle" style="margin-top:6px;">{TAGLINE_2}</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 4) 유틸: 파일 로딩
# =====================================================
def read_csv_best_effort(path: str) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "cp949"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise ValueError(f"CSV 인코딩을 읽지 못했어요: {path}")

def require_bench_files():
    missing = [f for f in REQUIRED_BENCH_FILES if not os.path.exists(f)]
    if missing:
        st.error(
            "필수 벤치마크 파일이 없어요.\n\n"
            f"- 누락: {', '.join(missing)}\n\n"
            "프로젝트 폴더에 두 파일을 같은 위치에 넣어주세요:\n"
            "- online viewing.csv\n- daily_usage.csv"
        )
        st.stop()

require_bench_files()

raw_view = read_csv_best_effort("online viewing.csv")
raw_usage = read_csv_best_effort("daily_usage.csv")

# =====================================================
# 🔥 5) (공공데이터) 벤치마크 정리 함수
#    - online viewing: 영상 시청시간 분포(%)
#    - daily_usage: 학습 목적 평균%, 비학습 목적 평균%
# =====================================================
def parse_viewing_distribution(df: pd.DataFrame) -> dict:
    """
    online viewing.csv 구조:
    - 0행이 사실상 '구간 라벨'
    - 1행부터 데이터
    원하는 출력: {"10분 미만": 3.7, ...} (전체-소계-소계의 2022 분포)
    """
    # 첫 줄(0행)에서 구간 라벨을 가져옴
    bins = list(df.iloc[0, 3:9].astype(str).values)
    # 전체 행 찾기: 응답자특성별(1)=전체, (2)=소계, (3)=소계
    mask = (df["응답자특성별(1)"] == "전체") & (df["응답자특성별(2)"] == "소계") & (df["응답자특성별(3)"] == "소계")
    row = df[mask]
    if row.empty:
        # fallback: 1행을 그냥 전체로 취급
        row = df.iloc[[1]]

    vals = row.iloc[0, 3:9].astype(float).values
    return dict(zip(bins, vals))

def parse_study_share(df: pd.DataFrame) -> tuple[float, float]:
    """
    daily_usage.csv 구조:
    - 0행: 목적 그룹명(일/학업/가사 관련 목적..., 이외 목적...)
    - 1행: 구간 라벨(0~20, 20~40..., 평균(%))
    - 2행부터 데이터
    목표: 전체-소계-소계의 '평균(%)' 2개를 꺼냄
      - 학습(일/학업/가사 관련 목적) 평균: 2022.5
      - 비학습(이외 목적) 평균: 2022.11
    """
    mask = (df["응답자특성별(1)"] == "전체") & (df["응답자특성별(2)"] == "소계") & (df["응답자특성별(3)"] == "소계")
    row = df[mask]
    if row.empty:
        row = df.iloc[[2]]

    # 컬럼 위치가 고정(파일 형태 기준)
    study_mean = float(row.iloc[0]["2022.5"])
    nonstudy_mean = float(row.iloc[0]["2022.11"])
    return study_mean, nonstudy_mean

BENCH_VIEW_DIST = parse_viewing_distribution(raw_view)          # 영상 시청시간 분포(%)
BENCH_STUDY_MEAN, BENCH_NONSTUDY_MEAN = parse_study_share(raw_usage)  # 학습/비학습 평균(%)

# =====================================================
# 🔥 6) 입력 카테고리(세부화 + 나중에 시각화 가능)
# =====================================================
CATEGORIES = [
    ("gaming",      "🎮 게임",              "게임 플레이/모바일 게임/콘솔"),
    ("youtube",     "📺 유튜브·영상",        "유튜브/넷플릭스/숏폼 포함"),
    ("social",      "📸 인스타·SNS",          "인스타/틱톡/DM/피드"),
    ("study_video", "🧠 동영상 강의(학습)",   "인강/강의/학습 영상"),
    ("creation",    "🎬 영상 제작",          "촬영/편집/업로드/자막/썸네일"),
    ("decorate",    "✨ 꾸미미·편집",        "스토리 꾸미기/프로필/스티커/템플릿"),
    ("chat",        "💬 채팅·메신저",        "카톡/DM/단체채팅"),
    ("music",       "🎧 음악",              "스트리밍/플리"),
    ("web",         "🌐 웹서핑",            "검색/커뮤니티/뉴스/쇼핑"),
]

# =====================================================
# 🔥 7) 추천 활동(영상 말고 다양화)
# =====================================================
OFFLINE_RECO_POOL = {
    "movement": ["산책 10분 🚶", "스트레칭 5분 🧘", "스쿼트 15회 🏋️", "계단 오르기 5분 🪜"],
    "eyes": ["20-20-20 눈 휴식 👀", "먼 곳 보기 2분 🌿", "물 마시고 창밖 보기 2분 💧"],
    "focus": ["책 10페이지 📖", "책상 정리 5분 🧹", "투두 3개 적기 ✍️", "타이머 15분 집중 ⏳"],
    "social": ["친구/가족 안부 한 줄 💬", "대화 산책 🚶‍♀️", "감사한 일 1개 공유 💛"],
    "creative": ["낙서/스케치 5분 🎨", "사진 찍기(밖에서) 📷", "짧은 일기 3줄 📝"],
    "calm": ["호흡 1분 🌬️", "음악 들으며 눈 감기 5분 🎧", "미니 명상 2분 🫧"],
}

# =====================================================
# 8) 기록 저장/불러오기(지난 기록 비교)
# =====================================================
LOG_FILE = "digi_balance_log.csv"

def load_local_log() -> pd.DataFrame:
    if os.path.exists(LOG_FILE):
        try:
            df = read_csv_best_effort(LOG_FILE)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_local_log(df: pd.DataFrame) -> bool:
    try:
        df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
        return True
    except Exception:
        return False

if "log_df" not in st.session_state:
    st.session_state["log_df"] = load_local_log()

# =====================================================
# 🔥 9) 점수/레벨 로직(학습/제작 덜 페널티)
# =====================================================
def minutes_sum(values: dict) -> int:
    return int(sum(max(0, int(v)) for v in values.values()))

def weighted_score(values: dict) -> int:
    w = {
        "gaming": 1.20,
        "youtube": 1.05,
        "social": 1.10,
        "study_video": 0.40,   # 학습은 덜 페널티
        "creation": 0.55,      # 제작도 덜 페널티
        "decorate": 0.90,
        "chat": 0.75,
        "music": 0.35,
        "web": 0.80,
    }
    total = 0.0
    for k, v in values.items():
        total += float(v) * w.get(k, 1.0)
    score = int(np.clip(total / 6.2, 0, 100))  # 0~100
    return score

def level_from_score(score: int) -> str:
    if score < 35: return "LOW"
    if score < 65: return "MEDIUM"
    return "HIGH"

def level_badge(level: str):
    if level == "LOW": return "🟢 안정", "good"
    if level == "MEDIUM": return "🟡 주의", "warn"
    return "🔴 과다", "bad"

def suggest_off_plan(level: str, total_min: int) -> str:
    if level == "LOW": return "추천: 90분 사용 → 10분 OFF"
    if level == "MEDIUM": return "추천: 60분 사용 → 15분 OFF"
    if total_min >= 420: return "추천: 40분 사용 → 20분 OFF (오늘은 강하게 쉬자)"
    return "추천: 45분 사용 → 20분 OFF"

def pick_recos(values: dict, level: str):
    top_key = max(values, key=lambda k: values.get(k, 0))
    recs = []

    if level == "HIGH": recs.append("📵 30분 OFF (알림 끄고 폰은 멀리)")
    elif level == "MEDIUM": recs.append("📵 20분 OFF (방해금지 켜기)")
    else: recs.append("📵 10분 OFF (쉬는 습관 만들기)")

    if top_key in ["gaming"]:
        recs += [np.random.choice(OFFLINE_RECO_POOL["movement"]), np.random.choice(OFFLINE_RECO_POOL["focus"])]
    elif top_key in ["youtube", "social"]:
        recs += [np.random.choice(OFFLINE_RECO_POOL["eyes"]), np.random.choice(OFFLINE_RECO_POOL["calm"])]
    elif top_key in ["study_video"]:
        recs += [np.random.choice(OFFLINE_RECO_POOL["focus"]), np.random.choice(OFFLINE_RECO_POOL["calm"])]
    elif top_key in ["creation", "decorate"]:
        recs += [np.random.choice(OFFLINE_RECO_POOL["creative"]), np.random.choice(OFFLINE_RECO_POOL["movement"])]
    else:
        recs += [np.random.choice(OFFLINE_RECO_POOL["calm"]), np.random.choice(OFFLINE_RECO_POOL["movement"])]

    recs.append(np.random.choice(OFFLINE_RECO_POOL["social"]))
    return recs, top_key

# =====================================================
# 🔥 10) 공공데이터(벤치마크) 기반 비교 함수
# =====================================================
def video_bucket(video_min: int) -> str:
    if video_min < 10: return "10분 미만"
    if video_min < 30: return "10분 이상~30분 미만"
    if video_min < 60: return "30분 이상~1시간 미만"
    if video_min < 120: return "1시간 이상~2시간 미만"
    if video_min < 360: return "2시간 이상~6시간 미만"
    return "6시간 이상"

def approx_percentile_from_dist(bucket: str, dist: dict) -> float:
    """
    분포(%)에서 내 구간이 ‘상위 어느 정도’인지 대략 계산(정확한 퍼센타일은 아니지만 비교용으로 충분)
    상위% ≈ 내 구간 이상 비율
    """
    order = [
        "10분 미만",
        "10분 이상~30분 미만",
        "30분 이상~1시간 미만",
        "1시간 이상~2시간 미만",
        "2시간 이상~6시간 미만",
        "6시간 이상",
    ]
    if bucket not in order:
        return np.nan
    idx = order.index(bucket)
    # bucket 이상(=더 많이 보는 구간) 합
    above = 0.0
    for b in order[idx:]:
        above += float(dist.get(b, 0.0))
    return above  # 예: 12.2 => 상위 약 12.2%쪽(많이 본 사람 비율)

def study_ratio(values: dict) -> float:
    total = minutes_sum(values)
    if total <= 0:
        return 0.0
    return float(values.get("study_video", 0) / total * 100.0)

# ==========================
# 🔥 11) 탭
# ==========================
tab1, tab2 = st.tabs(["✨ 오늘 기록", "📊 리포트·비교"])

# ==========================
# TAB 1: 오늘 기록
# ==========================
with tab1:
    # 🔥 11-1) 프로필(1.3번: 감성 추가)
    st.markdown('<div class="card"><div class="big">🧑‍🚀 내 프로필</div><div class="subtle">닉네임 + 아바타로 좀 더 앱처럼</div></div>', unsafe_allow_html=True)

    avatars = ["🧑‍🎤", "🧑‍🚀", "🧑‍💻", "🧑‍🎨", "🧑‍🍳", "🧑‍🏫", "🧑‍🌾", "🧑‍🔬", "🧑‍🎧"]
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.6, 1.2])
    with c1:
        nickname = st.text_input("닉네임", value="나", max_chars=12)
    with c2:
        avatar = st.selectbox("아바타", avatars, index=2)
    with c3:
        user_gender = st.segmented_control("성별", options=["남", "여", "기타/비공개"], default="기타/비공개")
    with c4:
        user_age = st.selectbox("나이", list(range(10, 20)), index=6)

    daytype = st.segmented_control("오늘은?", options=["주중", "주말"], default="주중")

    # 🔥 11-2) 디지털 활동(세부)
    st.markdown('<div class="card"><div class="big">📲 오늘의 디지털 활동</div><div class="subtle">분 단위로 세부 입력 → 나중에 자동 시각화</div></div>', unsafe_allow_html=True)

    values = {}
    left, right = st.columns(2)

    with left:
        values["gaming"] = st.slider("🎮 게임 (분)", 0, 600, 60, 5)
        values["youtube"] = st.slider("📺 유튜브·영상 (분)", 0, 600, 90, 5)
        values["social"] = st.slider("📸 인스타·SNS (분)", 0, 600, 60, 5)
        values["study_video"] = st.slider("🧠 동영상 강의(학습) (분)", 0, 600, 40, 5)

    with right:
        values["creation"] = st.slider("🎬 영상 제작 (분)", 0, 600, 0, 5)
        values["decorate"] = st.slider("✨ 꾸미미·편집 (분)", 0, 600, 10, 5)
        values["chat"] = st.slider("💬 채팅·메신저 (분)", 0, 600, 20, 5)
        values["music"] = st.slider("🎧 음악 (분)", 0, 600, 30, 5)
        values["web"] = st.slider("🌐 웹서핑 (분)", 0, 600, 20, 5)

    total_min = minutes_sum(values)
    score = weighted_score(values)
    level = level_from_score(score)
    badge, badge_class = level_badge(level)

    # 🔥 11-3) 학습/오락 비율 그래프(1번 추가)
    s_ratio = study_ratio(values)
    e_ratio = 100.0 - s_ratio

    st.markdown(
        f"""
        <div class="card">
          <div class="big">{avatar} {nickname}의 오늘 요약</div>
          <div style="margin-top:10px;">
            <span class="pill">총합 <b>{total_min}분</b></span>
            <span class="pill">밸런스 <b>{score}/100</b></span>
            <span class="pill {badge_class}">{badge}</span>
          </div>
          <div class="muted" style="margin-top:10px;">학습/제작은 덜 페널티로 계산돼요.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="card"><div class="big">📚 학습 vs 🎉 오락 비율</div><div class="muted">내가 어디에 시간을 쓰는지 한눈에</div></div>', unsafe_allow_html=True)
    ratio_df = pd.DataFrame({"비율(%)": [s_ratio, e_ratio]}, index=["학습(동영상 강의)", "오락/기타"])
    st.bar_chart(ratio_df)

    # 🔥 11-4) 공공데이터(벤치마크) 비교: 영상 시청 분포
    video_min = int(values["youtube"])
    bucket = video_bucket(video_min)
    top_share = approx_percentile_from_dist(bucket, BENCH_VIEW_DIST)

    st.markdown('<div class="card"><div class="big">📺 영상 시청 비교</div><div class="muted">내 영상 시청 시간(분)을 분포 구간으로 비교해요</div></div>', unsafe_allow_html=True)
    st.write(f"- 오늘 영상(유튜브·영상): **{video_min}분** → 구간: **{bucket}**")
    if not np.isnan(top_share):
        st.write(f"- 내 구간 이상(=나보다 많이 보는 사람 구간 포함) 비율: **약 {top_share:.1f}%**")
        st.caption("※ 분포 기반으로 ‘대략적 비교’만 제공합니다(정확한 퍼센타일 아님).")

    # 🔥 11-5) 공공데이터(벤치마크) 비교: 학습 비율 평균 비교
    st.markdown('<div class="card"><div class="big">🧠 학습 비율 비교</div><div class="muted">학습 목적 평균과 내 비율을 비교해요</div></div>', unsafe_allow_html=True)
    st.write(f"- 내 학습(동영상 강의) 비율: **{s_ratio:.1f}%**")
    st.write(f"- 벤치마크 학습 목적 평균: **{BENCH_STUDY_MEAN:.1f}%**  | 비학습 평균: **{BENCH_NONSTUDY_MEAN:.1f}%**")

    # 분석 버튼
    if st.button("🧠 오늘의 코칭 보기", use_container_width=True):
        st.markdown('<div class="card"><div class="big">🎯 오늘의 코칭</div></div>', unsafe_allow_html=True)

        # 오프 플랜
        st.markdown(
            f'<div class="card"><div class="big">⏱️ 오프 루틴</div><div class="muted">{suggest_off_plan(level, total_min)}</div></div>',
            unsafe_allow_html=True
        )

        recos, top_key = pick_recos(values, level)
        top_label = dict((k, v) for k, v, _ in CATEGORIES).get(top_key, top_key)

        st.markdown(
            f"""
            <div class="card">
              <div class="big">📍 오늘 TOP 패턴</div>
              <div class="muted"><b>{top_label}</b> 비중이 가장 커요. 이 패턴에 맞춰 추천을 골랐어요.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        for r in recos:
            st.markdown(f"<div class='card'><div class='big'>✅ {r}</div></div>", unsafe_allow_html=True)

        # 기록 저장(로컬 + 세션)
        today = date.today().isoformat()
        row = {
            "date": today,
            "nickname": nickname,
            "avatar": avatar,
            "age": user_age,
            "gender": user_gender,
            "daytype": daytype,
            "total_min": total_min,
            "score": score,
            "level": level,
            "video_bucket": bucket,
            "study_ratio": round(s_ratio, 2),
            **values
        }

        df = st.session_state["log_df"].copy()
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        # 같은 날짜면 최신으로 덮어쓰기
        df["date"] = df["date"].astype(str)
        df = df.drop_duplicates(subset=["date", "nickname"], keep="last").reset_index(drop=True)

        st.session_state["log_df"] = df
        save_local_log(df)

        st.success("저장 완료! ‘리포트·비교’ 탭에서 전 기록과 비교할 수 있어요.")

    st.caption("※ 기록은 앱 내부 CSV(digi_balance_log.csv)로도 저장 시도하며, 리포트에서 내려받을 수 있어요.")


# ==========================
# TAB 2: 리포트·비교(지난 기록 비교 기능)
# ==========================
with tab2:
    st.markdown('<div class="card"><div class="big">📊 리포트 · 지난 기록 비교</div><div class="subtle">전 기록과 비교해서 변화가 보이게</div></div>', unsafe_allow_html=True)

    log_df = st.session_state["log_df"].copy()
    if log_df.empty:
        st.info("아직 저장된 기록이 없어요. ‘오늘 기록’에서 코칭 보기까지 눌러 저장해보세요 🙂")
        st.stop()

    # 날짜 정리
    log_df["date"] = pd.to_datetime(log_df["date"], errors="coerce")
    log_df = log_df.dropna(subset=["date"]).sort_values("date")

    # 기록 목록
    st.markdown('<div class="card"><div class="big">🗂️ 기록 목록</div></div>', unsafe_allow_html=True)
    show_cols = ["date", "nickname", "total_min", "score", "level", "study_ratio", "youtube"]
    exist_cols = [c for c in show_cols if c in log_df.columns]
    st.dataframe(log_df[exist_cols], use_container_width=True, hide_index=True)

    # 🔥 12) 지난 기록 비교(선택일 vs 비교일)
    st.markdown('<div class="card"><div class="big">🆚 기록 비교</div><div class="muted">두 날짜를 선택해서 변화(분)를 확인해요</div></div>', unsafe_allow_html=True)

    nicknames = sorted(log_df["nickname"].dropna().unique().tolist())
    selected_nick = st.selectbox("비교할 닉네임", nicknames, index=len(nicknames)-1)

    user_df = log_df[log_df["nickname"] == selected_nick].copy()
    dates = user_df["date"].dt.date.astype(str).tolist()

    if len(dates) < 2:
        st.info("비교하려면 최소 2개의 기록이 필요해요. 오늘 기록을 며칠 더 쌓아보세요 🙂")
    else:
        c1, c2 = st.columns(2)
        with c1:
            a_date = st.selectbox("기준 날짜", dates, index=len(dates)-1)
        with c2:
            b_date = st.selectbox("비교 날짜", dates, index=max(len(dates)-2, 0))

        A = user_df[user_df["date"].dt.date.astype(str) == a_date].iloc[-1]
        B = user_df[user_df["date"].dt.date.astype(str) == b_date].iloc[-1]

        def delta(a, b):  # a - b
            return float(a) - float(b)

        # 총합/점수 변화
        st.markdown('<div class="card"><div class="big">📌 변화 요약</div></div>', unsafe_allow_html=True)
        st.write(f"- 총 디지털 시간 변화: **{delta(A['total_min'], B['total_min']):+.0f}분**")
        st.write(f"- 밸런스 점수 변화: **{delta(A['score'], B['score']):+.0f}점**")
        if "study_ratio" in user_df.columns:
            st.write(f"- 학습 비율 변화: **{delta(A['study_ratio'], B['study_ratio']):+.1f}%p**")

        # 카테고리별 변화
        cat_keys = [k for k, _, _ in CATEGORIES if k in user_df.columns]
        diffs = {k: delta(A.get(k, 0), B.get(k, 0)) for k in cat_keys}
        diffs_df = pd.DataFrame({"변화(분)": diffs}).T.sort_values("변화(분)", ascending=False)

        st.markdown('<div class="card"><div class="big">📲 카테고리별 변화(분)</div><div class="muted">+면 늘고, -면 줄었어요</div></div>', unsafe_allow_html=True)
        st.bar_chart(diffs_df)

        # 최신 카테고리 파이
        st.markdown('<div class="card"><div class="big">🍰 선택 날짜 카테고리 비중</div><div class="muted">기준 날짜(A)의 비중</div></div>', unsafe_allow_html=True)
        values_a = [int(A.get(k, 0)) for k in cat_keys]
        labels = [label for k, label, _ in CATEGORIES if k in cat_keys]
        if sum(values_a) == 0:
            st.info("선택 날짜 기록에 시간이 없어요.")
        else:
            plt.figure()
            plt.pie(values_a, labels=labels, autopct="%1.0f%%")
            st.pyplot(plt.gcf(), clear_figure=True)

    # 추세 그래프
    st.markdown('<div class="card"><div class="big">📈 추세</div><div class="muted">총합/점수 변화</div></div>', unsafe_allow_html=True)
    plt.figure()
    plt.plot(log_df["date"], log_df["total_min"], marker="o", label="Total minutes")
    plt.xlabel("Date")
    plt.ylabel("Minutes")
    plt.legend()
    st.pyplot(plt.gcf(), clear_figure=True)

    plt.figure()
    plt.plot(log_df["date"], log_df["score"], marker="o", label="Balance score (0~100)")
    plt.xlabel("Date")
    plt.ylabel("Score")
    plt.legend()
    st.pyplot(plt.gcf(), clear_figure=True)

    # CSV 다운로드
    st.download_button(
        "⬇️ 내 기록 CSV 다운로드",
        data=log_df.assign(date=log_df["date"].dt.date.astype(str)).to_csv(index=False, encoding="utf-8-sig"),
        file_name="digi_balance_log.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.caption("팁: Streamlit Cloud는 저장이 초기화될 수 있으니 기록 CSV는 주기적으로 다운로드해두세요.")
