import os, time, json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# --- 1. 설정 및 초기화 ---
st.set_page_config(page_title="AI 끝말잇기", page_icon="💬", layout="centered")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# 세션 상태 관리
if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "remaining_time" not in st.session_state:
    st.session_state.remaining_time = 30
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "error_msg" not in st.session_state:
    st.session_state.error_msg = ""
if "processing" not in st.session_state:
    st.session_state.processing = False
if "ai_response_pending" not in st.session_state:
    st.session_state.ai_response_pending = False
if "pending_user_word" not in st.session_state:
    st.session_state.pending_user_word = None

# --- 랭크 시스템 함수 ---
def load_rankings():
    try:
        if os.path.exists("rank.json"):
            with open("rank.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except (json.JSONDecodeError, Exception):
        return []

def save_ranking(name, score):
    rankings = load_rankings()
    rankings.append({
        "name": name,
        "score": score,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    rankings.sort(key=lambda x: x["score"], reverse=True)
    rankings = rankings[:10]  # 상위 10개만 유지
    with open("rank.json", "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

# --- 2. 두음법칙 로직 ---
def get_valid_starts(last_char):
    """
    두음법칙을 적용하여 가능한 시작 글자들을 반환
    - ㄴ, ㄹ이 단어 첫머리에 올 때 ㅇ 또는 탈락
    - 예: 냥→양, 녀→여, 료→요, 리→이
    """
    starts = [last_char]
    code = ord(last_char)
    
    if 0xAC00 <= code <= 0xD7A3:
        char_code = code - 0xAC00
        cho = char_code // (21 * 28)  # 초성
        jung = (char_code % (21 * 28)) // 28  # 중성
        jong = char_code % 28  # 종성
        
        # ㄴ(2) 초성일 때
        if cho == 2:
            # ㄴ + (ㅏ, ㅐ, ㅑ, ㅒ, ㅓ, ㅔ, ㅕ, ㅖ, ㅗ, ㅛ, ㅜ, ㅠ, ㅡ, ㅣ) → ㅇ으로 변환
            if jung in [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 17, 18, 20]:
                starts.append(chr(0xAC00 + (11 * 21 * 28) + (jung * 28) + jong))
        
        # ㄹ(5) 초성일 때
        elif cho == 5:
            # ㄹ + (ㅑ, ㅒ, ㅕ, ㅖ, ㅛ, ㅠ, ㅣ) → ㅇ으로 변환
            if jung in [2, 3, 6, 7, 12, 17, 20]:
                starts.append(chr(0xAC00 + (11 * 21 * 28) + (jung * 28) + jong))
            # ㄹ + (ㅏ, ㅐ, ㅓ, ㅔ, ㅗ, ㅜ, ㅡ) → ㄴ으로 변환
            if jung in [0, 1, 4, 5, 8, 13, 18]:
                starts.append(chr(0xAC00 + (2 * 21 * 28) + (jung * 28) + jong))
    
    return list(set(starts))

def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 3. UI 레이아웃 ---
# 사이드바에 랭킹 표시
with st.sidebar:
    st.header("🏆 명예의 전당")
    rankings = load_rankings()
    if rankings:
        for i, rank in enumerate(rankings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            st.write(f"{medal} **{rank['name']}** - {rank['score']}개")
            st.caption(rank['date'])
    else:
        st.info("아직 기록이 없습니다!")

st.title("AI 끝말잇기")
st.markdown("사전 없이 AI와 직접 대결하세요!")

# 상단 상태바
status_area = st.empty()
if not st.session_state.game_over:
    with status_area.container():
        cols = st.columns([4, 1])
        cols[0].progress(max(0, st.session_state.remaining_time / 30))
        cols[1].write(f"⏳ **{st.session_state.remaining_time}초**")

# 채팅창
chat_placeholder = st.container(height=450)
with chat_placeholder:
    if not st.session_state.word_list and not st.session_state.pending_user_word:
        st.info("단어를 입력하여 게임을 시작하세요.")
    
    # 이미 확정된 단어들 표시
    for i, word in enumerate(st.session_state.word_list):
        role = "user" if i % 2 == 0 else "assistant"
        st.chat_message(role).write(word)
    
    # pending 중인 사용자 단어 표시
    if st.session_state.pending_user_word:
        st.chat_message("user").write(st.session_state.pending_user_word)

# 에러 메시지 영역
error_area = st.empty()
if st.session_state.error_msg:
    error_area.warning(st.session_state.error_msg)

# --- 4. 메인 로직 ---
if not st.session_state.game_over:
    # AI 응답 처리
    if st.session_state.ai_response_pending and st.session_state.pending_user_word:
        user_input = st.session_state.pending_user_word
        
        with st.spinner("AI가 생각 중..."):
            valid_starts_for_ai = get_valid_starts(user_input[-1])
            prompt = (
                f"한국어 끝말잇기 게임 중이야. 규칙은 다음과 같아.\n"
                f"1. 사용자가 방금 입력한 단어: '{user_input}'\n"
                f"2. 규칙: 이 단어가 실제로 존재하는 한국어 명사인지 판단해주고 외래어도 허용해줘.\n"
                f"3. 만약 부적절하다면 'INVALID:이유'라고 답해.\n"
                f"4. 적절하다면, 다음 글자 중 하나로 시작하는 한국어 명사를 대답해: {', '.join(valid_starts_for_ai)}\n"
                f"   두음법칙 예시:\n"
                f"   - '냥'→'양', '녀'→'여', '뇨'→'요', '뉴'→'유', '니'→'이'\n"
                f"   - '랴'→'야', '려'→'여', '례'→'예', '료'→'요', '류'→'유', '리'→'이'\n"
                f"   - '라'→'나', '래'→'내', '로'→'노', '루'→'누', '르'→'느'\n"
                f"5. 만약 네가 단어를 찾지 못하겠다면 'I_LOSE'라고 답해.\n"
                f"6. 이미 사용된 단어들 (절대 이 중에서 선택하지 마): {st.session_state.word_list}\n"
                f"7. 중요: 위 6번 리스트에 있는 단어는 절대 사용하면 안 돼. 새로운 단어만 말해.\n"
                "단어만 말하고 다른 설명은 하지 마."
            )

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "너는 끝말잇기 심판이자 플레이어야."},
                              {"role": "user", "content": prompt}]
                )
                res_text = response.choices[0].message.content.strip()

                if res_text.startswith("INVALID"):
                    reason = res_text.split(":")[-1]
                    st.session_state.error_msg = f"❌ {reason}"
                elif res_text == "I_LOSE":
                    st.session_state.word_list.append(user_input)
                    st.session_state.error_msg = "🎉 AI가 단어를 찾지 못해 패배를 선언했습니다!"
                    st.session_state.game_over = True
                else:
                    # AI가 중복 단어를 말했는지 체크
                    if res_text in st.session_state.word_list or res_text == user_input:
                        st.session_state.word_list.append(user_input)
                        st.session_state.error_msg = "🎉 AI가 중복된 단어를 말해서 패배했습니다!"
                        st.session_state.game_over = True
                    else:
                        st.session_state.word_list.append(user_input)
                        st.session_state.word_list.append(res_text)
                        st.session_state.remaining_time = 30
            except Exception as e:
                st.session_state.error_msg = f"AI 오류: {e}"
            
            st.session_state.ai_response_pending = False
            st.session_state.pending_user_word = None
            st.rerun()
    
    user_input = st.chat_input("단어를 입력하세요...", disabled=st.session_state.ai_response_pending)

    if user_input and not st.session_state.ai_response_pending:
        user_input = user_input.strip()
        last_word = st.session_state.word_list[-1] if st.session_state.word_list else None
        valid_starts = get_valid_starts(last_word[-1]) if last_word else []

        # [기본 검증] 중복 및 두음법칙
        if user_input in st.session_state.word_list:
            st.session_state.error_msg = f"❌ '{user_input}'은(는) 이미 사용되었습니다!"
            st.rerun()
        elif last_word and (user_input[0] not in valid_starts):
            st.session_state.error_msg = f"❌ '{'/'.join(valid_starts)}'(으)로 시작해야 합니다!"
            st.rerun()
        else:
            # 사용자 단어를 pending으로 저장 (아직 리스트에 추가하지 않음)
            st.session_state.pending_user_word = user_input
            st.session_state.error_msg = ""
            st.session_state.ai_response_pending = True
            st.rerun()

    # 타이머
    if st.session_state.word_list and not st.session_state.ai_response_pending:
        time.sleep(1)
        st.session_state.remaining_time -= 1
        if st.session_state.remaining_time <= 0:
            st.session_state.game_over = True
        st.rerun()

# --- 5. 게임 종료 ---
else:
    status_area.empty()
    st.error("🎮 GAME OVER")
    score = len(st.session_state.word_list)
    st.markdown(f"### 최종 점수: {score} 단어")
    
    # 랭킹 등록
    if "rank_saved" not in st.session_state:
        name = st.text_input("이름을 입력하세요:", max_chars=20)
        if st.button("랭킹 등록", use_container_width=True) and name:
            save_ranking(name.strip(), score)
            st.session_state.rank_saved = True
            st.success("랭킹에 등록되었습니다!")
            time.sleep(1)
            st.rerun()
    
    if st.button("다시 시작하기", use_container_width=True):
        reset_game()