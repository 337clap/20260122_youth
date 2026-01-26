
import os
from datetime import date, datetime
import time

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =====================================================
# 🔥 0) 필수 벤치마크 파일(선택 아님)
# =====================================================
REQUIRED_BENCH_FILES = ["online viewing.csv", "daily_usage.csv"]
LOG_FILE = "digi_balance_log.csv"


# =====================================================
# 🔥 1) 브랜딩(여기만 바꾸면 전체 톤 바뀜)
# =====================================================
APP_NAME = "DIGI BALANCE"
TAGLINE_1 = "나를 위한 스마트한 디지털 습관"
TAGLINE_2 = "오늘 기록하고, 내 패턴을 예쁘게 확인해요 ✨"

st.set_page_config(page_title=APP_NAME, page_icon="🌱", layout="centered")


# =====================================================
# 🔥 2) 트렌디 CSS (카드/필/간격/모바일 느낌)
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
        background: rgba(250,250,250,0.88);
        margin-bottom: 14px;
      }
      .pill {
        display:inline-block; padding:6px 10px; border-radius:999px;
        background: rgba(0,0,0,0.05); margin-right:6px; font-size: 0.92rem;
      }
      .big {font-size: 1.25rem; font-weight: 900;}
      .muted {color:#6f6f6f;}
      .good {color:#138a3d; font-weight:900;}
      .warn {color:#c77b00; font-weight:900;}
      .bad  {color:#c0362c; font-weight:900;}
      .kpi-grid {display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px;}
      .kpi {border: 1px solid rgba(0,0,0,0.06); border-radius: 16px; padding: 14px; background: rgba(255,255,255,0.7);}
      .kpi .label {color:#7a7a7a; font-size: 0.92rem;}
      .kpi .value {font-size: 1.35rem; font-weight: 900; margin-top: 4px;}
      .tiny {font-size: 0.9rem;}
      @media (max-width: 720px) {
        .kpi-grid {grid-template-columns: 1fr;}
      }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 🔥 3) 헤더 (※ “공공데이터” 문구 없음)
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
# 유틸: 파일 로딩/체크
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
            "필수 파일이 없어요.\n\n"
            f"- 누락: {', '.join(missing)}\n\n"
            "프로젝트 폴더(app.py와 같은 위치)에 아래 2개 파일을 넣어주세요:\n"
            "- online viewing.csv\n- daily_usage.csv"
        )
        st.stop()

require_bench_files()

raw_view = read_csv_best_effort("online viewing.csv")
raw_usage = read_csv_best_effort("daily_usage.csv")


# =====================================================
# 🔥 4) 입력 카테고리(세부화 / 시각화 가능)
# =====================================================
CATEGORIES = [
    ("gaming",      "🎮 게임",               "게임 플레이/모바일 게임/콘솔"),
    ("youtube",     "📺 유튜브·영상",         "유튜브/넷플릭스/숏폼 포함"),
    ("social",      "📸 인스타·SNS",           "인스타/틱톡/DM/피드"),
    ("study_video", "🧠 동영상 강의(학습)",    "인강/강의/학습 영상"),
    ("creation",    "🎬 영상 제작",           "촬영/편집/업로드/자막/썸네일"),
    ("decorate",    "✨ 꾸미미·편집",         "스토리 꾸미기/프로필/스티커/템플릿"),
    ("chat",        "💬 채팅·메신저",         "카톡/DM/단체채팅"),
    ("music",       "🎧 음악",               "스트리밍/플리"),
    ("web",         "🌐 웹서핑",             "검색/커뮤니티/뉴스/쇼핑"),
]
LABEL_MAP = {k: label for k, label, _ in CATEGORIES}


# =====================================================
# 🔥 5) 추천 활동 풀(영상 말고 다양)
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
# 🔥 6) 벤치마크 파싱 (화면에 “공공데이터”라는 말은 안 씀)
# =====================================================
def parse_viewing_distribution(df: pd.DataFrame) -> dict:
    """
    online viewing.csv:
    - 0행에 구간 라벨
    - 전체/소계/소계 행의 2022 분포(%) 사용
    """
    bins = list(df.iloc[0, 3:9].astype(str).values)
    mask = (df["응답자특성별(1)"] == "전체") & (df["응답자특성별(2)"] == "소계") & (df["응답자특성별(3)"] == "소계")
    row = df[mask]
    if row.empty:
        row = df.iloc[[1]]
    vals = row.iloc[0, 3:9].astype(float).values
    return dict(zip(bins, vals))

def parse_study_share(df: pd.DataFrame) -> tuple[float, float]:
    """
    daily_usage.csv:
    전체/소계/소계 행의 평균(%)
    - 2022.5: 학습 목적 평균(%)
    - 2022.11: 비학습 목적 평균(%)
    """
    mask = (df["응답자특성별(1)"] == "전체") & (df["응답자특성별(2)"] == "소계") & (df["응답자특성별(3)"] == "소계")
    row = df[mask]
    if row.empty:
        row = df.iloc[[2]]
    study_mean = float(row.iloc[0]["2022.5"])
    nonstudy_mean = float(row.iloc[0]["2022.11"])
    return study_mean, nonstudy_mean

BENCH_VIEW_DIST = parse_viewing_distribution(raw_view)
BENCH_STUDY_MEAN, BENCH_NONSTUDY_MEAN = parse_study_share(raw_usage)


# =====================================================
# 🔥 7) 점수/레벨 로직(학습/제작 덜 페널티)
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
    score = int(np.clip(total / 6.2, 0, 100))
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

def study_ratio(values: dict) -> float:
    total = minutes_sum(values)
    if total <= 0:
        return 0.0
    return float(values.get("study_video", 0) / total * 100.0)


# =====================================================
# 🔥 8) 벤치마크 비교용 함수(자연스러운 근거 한 줄)
# =====================================================
def video_bucket(video_min: int) -> str:
    if video_min < 10: return "10분 미만"
    if video_min < 30: return "10분 이상~30분 미만"
    if video_min < 60: return "30분 이상~1시간 미만"
    if video_min < 120: return "1시간 이상~2시간 미만"
    if video_min < 360: return "2시간 이상~6시간 미만"
    return "6시간 이상"

def approx_above_share(bucket: str, dist: dict) -> float:
    """
    분포(%)에서 '내 구간 이상(더 많이 보는 구간 포함)' 비율을 계산
    → 화면에는 “근거 한 줄”로만 보여줌
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
        return float("nan")
    idx = order.index(bucket)
    return float(sum(float(dist.get(b, 0.0)) for b in order[idx:]))


# =====================================================
# 🔥 9) 추천/퀘스트 생성 (3번 기능)
# =====================================================
def pick_recos(values: dict, level: str):
    top_key = max(values, key=lambda k: values.get(k, 0))
    recs = []

    # OFF(디지털 스위치 오프 느낌)
    if level == "HIGH":
        recs.append("📵 30분 OFF (알림 끄고 폰은 멀리)")
    elif level == "MEDIUM":
        recs.append("📵 20분 OFF (방해금지 켜기)")
    else:
        recs.append("📵 10분 OFF (쉬는 습관 만들기)")

    # 패턴 맞춤
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

    # 하나 더
    recs.append(np.random.choice(OFFLINE_RECO_POOL["social"]))
    return recs, top_key


# =====================================================
# 10) 기록 저장/로드(지난 기록 비교용)
# =====================================================
def load_local_log() -> pd.DataFrame:
    if os.path.exists(LOG_FILE):
        try:
            return read_csv_best_effort(LOG_FILE)
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
# 🔥 11) 탭
# =====================================================
tab1, tab2 = st.tabs(["✨ 오늘 기록", "📊 리포트·비교"])


# =====================================================
# TAB 1: 오늘 기록
# =====================================================
with tab1:
    # (1) 무드 체크 + (프로필 트렌디)
    st.markdown(
        "<div class='card'><div class='big'>🧑‍🚀 내 프로필</div><div class='subtle'>닉네임 + 아바타 + 오늘 컨디션</div></div>",
        unsafe_allow_html=True
    )

    avatars = ["🧑‍🎤", "🧑‍🚀", "🧑‍💻", "🧑‍🎨", "🧑‍🍳", "🧑‍🏫", "🧑‍🔬", "🧑‍🎧", "🧑‍🌿"]
    c1, c2, c3, c4 = st.columns([1.3, 1.1, 1.6, 1.1])
    with c1:
        nickname = st.text_input("닉네임", value="나", max_chars=12)
    with c2:
        avatar = st.selectbox("아바타", avatars, index=1)
    with c3:
        gender = st.segmented_control("성별", options=["남", "여", "기타/비공개"], default="기타/비공개")
    with c4:
        age = st.selectbox("나이", list(range(10, 20)), index=6)

    daytype = st.segmented_control("오늘은?", options=["주중", "주말"], default="주중")

    # 🔥 (1) 무드 체크
    st.markdown("<div class='card'><div class='big'>🫧 오늘 컨디션</div><div class='subtle'>한 줄만 체크해도 패턴이 더 잘 보여요</div></div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        mood = st.selectbox("기분", ["🙂 좋아", "😐 보통", "🙁 별로"])
    with m2:
        focus = st.selectbox("집중", ["🔥 잘됨", "➖ 보통", "🫥 안됨"])
    with m3:
        sleep = st.selectbox("수면", ["😴 충분", "😪 보통", "🥱 부족"])

    # 디지털 활동 입력(세부)
    st.markdown("<div class='card'><div class='big'>📲 오늘의 디지털 활동</div><div class='subtle'>분 단위로 세부 입력 → 자동 분석</div></div>", unsafe_allow_html=True)

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

    s_ratio = study_ratio(values)
    e_ratio = 100.0 - s_ratio

    # KPI 카드
    st.markdown(
        f"""
        <div class="card">
          <div class="big">{avatar} {nickname}의 오늘 요약</div>
          <div style="margin-top:10px;">
            <span class="pill">총합 <b>{total_min}분</b></span>
            <span class="pill">밸런스 <b>{score}/100</b></span>
            <span class="pill {badge_class}">{badge}</span>
          </div>
          <div class="kpi-grid" style="margin-top:12px;">
            <div class="kpi"><div class="label">학습 비율</div><div class="value">{s_ratio:.0f}%</div></div>
            <div class="kpi"><div class="label">오락/기타</div><div class="value">{e_ratio:.0f}%</div></div>
            <div class="kpi"><div class="label">추천 루틴</div><div class="value">{suggest_off_plan(level, total_min).split('추천: ')[-1]}</div></div>
          </div>
          <div class="muted tiny" style="margin-top:10px;">학습/제작은 덜 페널티로 계산돼요.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # (5) TOP3 자동 문장
    sorted_cats = sorted(values.items(), key=lambda x: x[1], reverse=True)
    top3 = [(k, v) for k, v in sorted_cats if v > 0][:3]
    top3_text = ", ".join([f"{LABEL_MAP.get(k, k)} {int(v)}분" for k, v in top3]) if top3 else "입력된 활동이 거의 없어요"
    st.markdown(
        f"<div class='card'><div class='big'>🧾 오늘 TOP 3</div><div class='muted'>{top3_text}</div></div>",
        unsafe_allow_html=True
    )

    # (1) 학습 vs 오락 비율 그래프
    st.markdown("<div class='card'><div class='big'>📚 학습 vs 🎉 오락 비율</div><div class='muted'>내 시간의 방향을 한눈에</div></div>", unsafe_allow_html=True)
    ratio_df = pd.DataFrame({"비율(%)": [s_ratio, e_ratio]}, index=["학습(동영상 강의)", "오락/기타"])
    st.bar_chart(ratio_df)

    # (8) “근거 한 줄” — 자연스러운 벤치마크 표시(공공데이터 언급 없음)
    video_min = int(values["youtube"])
    bucket = video_bucket(video_min)
    above_share = approx_above_share(bucket, BENCH_VIEW_DIST)

    st.markdown("<div class='card'><div class='big'>📌 오늘의 비교 포인트</div><div class='muted'>내 기록이 어느 쪽에 가까운지 참고용으로 보여줘요</div></div>", unsafe_allow_html=True)
    st.write(f"- 영상 시청: **{video_min}분** → 구간 **{bucket}**")
    if not np.isnan(above_share):
        st.write(f"- 같은 구간 이상(더 많이 보는 쪽 포함) 비율: **약 {above_share:.1f}%**")
        st.caption("※ 분포 기반의 참고 지표(정확한 퍼센타일은 아님)")

    # 학습비율 벤치마크 한 줄
    st.write(f"- 학습 비율: **{s_ratio:.1f}%** (참고 평균: 학습 **{BENCH_STUDY_MEAN:.1f}%**, 비학습 **{BENCH_NONSTUDY_MEAN:.1f}%**)")

    # =================================================
    # 분석/코칭
    # =================================================
    if st.button("🧠 오늘 코칭 받기", use_container_width=True):
        st.markdown("<div class='card'><div class='big'>🎯 오늘의 코칭</div><div class='muted'>오늘 패턴에 맞춘 퀘스트를 준비했어요</div></div>", unsafe_allow_html=True)

        # 추천 생성
        recos, top_key = pick_recos(values, level)
        top_label = LABEL_MAP.get(top_key, top_key)

        st.markdown(
            f"""
            <div class="card">
              <div class="big">📍 오늘 TOP 패턴</div>
              <div class="muted"><b>{top_label}</b> 비중이 가장 커요. 그래서 이 패턴에 맞춘 추천을 골랐어요.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # (3) 퀘스트 체크(완료 체크)
        st.markdown("<div class='card'><div class='big'>✅ 오늘의 퀘스트</div><div class='muted'>완료하면 체크해보자!</div></div>", unsafe_allow_html=True)
        quest_done = 0
        quest_keys = []
        today_key = date.today().isoformat()
        for i, r in enumerate(recos, 1):
            key = f"quest_{today_key}_{nickname}_{i}"
            quest_keys.append(key)
            checked = st.checkbox(f"퀘스트 {i}: {r}", key=key)
            quest_done += 1 if checked else 0

        if quest_done == len(recos):
            st.success("완벽해요! 오늘 퀘스트 올클리어 🎉")
            st.balloons()
        elif quest_done > 0:
            st.info(f"좋아요! {quest_done}/{len(recos)}개 완료했어요 👏")

        # (7) OFF 타이머 (간단 + 실제 카운트다운)
        st.markdown("<div class='card'><div class='big'>⏳ OFF 타이머</div><div class='muted'>짧게 쉬고 돌아오면 집중이 확 올라가요</div></div>", unsafe_allow_html=True)
        minutes = st.select_slider("타이머 길이(분)", options=[5, 10, 15, 20, 30], value=10)

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            start_timer = st.button("타이머 시작")
        with col_t2:
            fast_demo = st.button("데모(10초)")  # 테스트용

        if start_timer or fast_demo:
            seconds = 10 if fast_demo else int(minutes * 60)
            ph = st.empty()
            end = time.time() + seconds
            while True:
                remaining = int(end - time.time())
                if remaining <= 0:
                    break
                mm = remaining // 60
                ss = remaining % 60
                ph.info(f"📵 OFF 중… {mm:02d}:{ss:02d}")
                time.sleep(1)
            ph.success("끝! 돌아온 걸 환영해요 ✨ (물 한 잔 추천 💧)")
            st.toast("OFF 완료 🎉", icon="🌱")

        # 기록 저장(로컬 + 세션)
        now = datetime.now().strftime("%H:%M:%S")
        row = {
            "date": date.today().isoformat(),
            "time": now,
            "nickname": nickname,
            "avatar": avatar,
            "age": age,
            "gender": gender,
            "daytype": daytype,
            "mood": mood,
            "focus": focus,
            "sleep": sleep,
            "total_min": total_min,
            "score": score,
            "level": level,
            "study_ratio": round(s_ratio, 2),
            "video_bucket": bucket,
            "video_min": video_min,
            "bench_above_share": round(float(above_share), 2) if not np.isnan(above_share) else "",
            "bench_study_mean": round(BENCH_STUDY_MEAN, 2),
            **values
        }

        df = st.session_state["log_df"].copy()
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        # 같은 날짜+닉네임이면 최신 기록으로 덮어쓰기(옵션)
        # df = df.drop_duplicates(subset=["date", "nickname"], keep="last").reset_index(drop=True)

        st.session_state["log_df"] = df
        save_local_log(df)

        st.success("저장 완료! ‘리포트·비교’ 탭에서 지난 기록과 비교할 수 있어요.")

    st.caption("※ 기록은 로컬 CSV(digi_balance_log.csv)로 저장을 시도하며, 리포트에서 내려받을 수 있어요.")


# =====================================================
# TAB 2: 리포트·비교 (지난 기록 비교)
# =====================================================
with tab2:
    st.markdown("<div class='card'><div class='big'>📊 리포트 · 지난 기록 비교</div><div class='subtle'>전 기록과 비교해서 변화가 보이게</div></div>", unsafe_allow_html=True)

    log_df = st.session_state["log_df"].copy()
    if log_df.empty:
        st.info("아직 저장된 기록이 없어요. ‘오늘 기록’에서 코칭 받기까지 눌러 저장해보세요 🙂")
        st.stop()

    # 날짜 정리
    log_df["date"] = pd.to_datetime(log_df["date"], errors="coerce")
    log_df = log_df.dropna(subset=["date"]).sort_values("date")

    # 기록 목록(핵심만)
    st.markdown("<div class='card'><div class='big'>🗂️ 기록 목록</div><div class='muted'>최근 기록부터 쌓여요</div></div>", unsafe_allow_html=True)
    cols = [c for c in ["date","time","nickname","total_min","score","level","study_ratio","mood","sleep"] if c in log_df.columns]
    st.dataframe(log_df[cols].sort_values(["date","time"], ascending=[False, False]), use_container_width=True, hide_index=True)

    # 닉네임 선택
    st.markdown("<div class='card'><div class='big'>🆚 기록 비교</div><div class='muted'>두 날짜를 선택해서 변화(분)를 확인해요</div></div>", unsafe_allow_html=True)
    nicknames = sorted(log_df["nickname"].dropna().unique().tolist())
    selected_nick = st.selectbox("비교할 닉네임", nicknames, index=len(nicknames)-1)

    user_df = log_df[log_df["nickname"] == selected_nick].copy().sort_values(["date","time"])
    user_df["date_str"] = user_df["date"].dt.date.astype(str)

    dates = user_df["date_str"].unique().tolist()
    if len(dates) < 2:
        st.info("비교하려면 최소 2일 기록이 필요해요. 며칠만 더 기록해보자 🙂")
    else:
        c1, c2 = st.columns(2)
        with c1:
            a_date = st.selectbox("기준 날짜(A)", dates, index=len(dates)-1)
        with c2:
            b_date = st.selectbox("비교 날짜(B)", dates, index=max(len(dates)-2, 0))

        A = user_df[user_df["date_str"] == a_date].iloc[-1]
        B = user_df[user_df["date_str"] == b_date].iloc[-1]

        def delta(a, b):
            try:
                return float(a) - float(b)
            except Exception:
                return np.nan

        st.markdown("<div class='card'><div class='big'>📌 변화 요약</div></div>", unsafe_allow_html=True)
        st.write(f"- 총 디지털 시간 변화: **{delta(A.get('total_min',0), B.get('total_min',0)):+.0f}분**")
        st.write(f"- 밸런스 점수 변화: **{delta(A.get('score',0), B.get('score',0)):+.0f}점**")
        if "study_ratio" in user_df.columns:
            st.write(f"- 학습 비율 변화: **{delta(A.get('study_ratio',0), B.get('study_ratio',0)):+.1f}%p**")
        if "mood" in user_df.columns:
            st.write(f"- 기분: **{B.get('mood','')} → {A.get('mood','')}**")
        if "sleep" in user_df.columns:
            st.write(f"- 수면: **{B.get('sleep','')} → {A.get('sleep','')}**")

        # 카테고리별 변화
        cat_keys = [k for k, _, _ in CATEGORIES if k in user_df.columns]
        diffs = {LABEL_MAP.get(k, k): delta(A.get(k, 0), B.get(k, 0)) for k in cat_keys}
        diffs_df = pd.DataFrame({"변화(분)": diffs}).sort_values("변화(분)", ascending=False)

        st.markdown("<div class='card'><div class='big'>📲 카테고리별 변화(분)</div><div class='muted'>+면 늘고, -면 줄었어요</div></div>", unsafe_allow_html=True)
        st.bar_chart(diffs_df)

        # A일 카테고리 파이
        st.markdown("<div class='card'><div class='big'>🍰 기준 날짜(A) 카테고리 비중</div></div>", unsafe_allow_html=True)
        values_a = [int(A.get(k, 0)) for k in cat_keys]
        labels = [LABEL_MAP.get(k, k) for k in cat_keys]
        if sum(values_a) == 0:
            st.info("기준 날짜 기록에 시간이 없어요.")
        else:
            plt.figure()
            plt.pie(values_a, labels=labels, autopct="%1.0f%%")
            st.pyplot(plt.gcf(), clear_figure=True)

    # 추세 그래프(닉네임 기준)
    st.markdown("<div class='card'><div class='big'>📈 추세</div><div class='muted'>총합/점수 변화 (선택 닉네임)</div></div>", unsafe_allow_html=True)
    plot_df = user_df.copy()
    plt.figure()
    plt.plot(plot_df["date"], plot_df["total_min"], marker="o")
    plt.xlabel("Date")
    plt.ylabel("Minutes")
    st.pyplot(plt.gcf(), clear_figure=True)

    plt.figure()
    plt.plot(plot_df["date"], plot_df["score"], marker="o")
    plt.xlabel("Date")
    plt.ylabel("Score")
    st.pyplot(plt.gcf(), clear_figure=True)

    # CSV 다운로드
    st.download_button(
        "⬇️ 내 기록 CSV 다운로드",
        data=log_df.assign(date=log_df["date"].dt.date.astype(str)).to_csv(index=False, encoding="utf-8-sig"),
        file_name="digi_balance_log.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.caption("팁: Streamlit Cloud는 저장이 초기화될 수 있으니, 기록 CSV는 가끔 내려받아 보관해두면 좋아요.")
