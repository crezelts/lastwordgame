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
if "verified_words" not in st.session_state:
    st.session_state.verified_words = set()
if "is_ai_turn" not in st.session_state:
    st.session_state.is_ai_turn = False
if "current_user_word" not in st.session_state:
    st.session_state.current_user_word = None

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
    rankings = rankings[:10]
    with open("rank.json", "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

# --- 2. 두음법칙 로직 ---
def get_valid_starts(last_char):
    starts = [last_char]
    code = ord(last_char)
    
    if 0xAC00 <= code <= 0xD7A3:
        char_code = code - 0xAC00
        cho = char_code // (21 * 28)
        jung = (char_code % (21 * 28)) // 28
        jong = char_code % 28
        
        if cho == 2:
            if jung in [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 17, 18, 20]:
                starts.append(chr(0xAC00 + (11 * 21 * 28) + (jung * 28) + jong))
        
        elif cho == 5:
            if jung in [2, 3, 6, 7, 12, 17, 20]:
                starts.append(chr(0xAC00 + (11 * 21 * 28) + (jung * 28) + jong))
            if jung in [0, 1, 4, 5, 8, 13, 18]:
                starts.append(chr(0xAC00 + (2 * 21 * 28) + (jung * 28) + jong))
    
    return list(set(starts))

# --- 3. 단어 검증 함수 ---
def verify_word_with_search(word: str) -> tuple[bool, str]:
    if word in st.session_state.verified_words:
        return True, "검증 완료 (캐시)"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """너는 한국어 단어 검증 전문가다. 
반드시 네이버 국어사전(https://ko.dict.naver.com)을 실제로 검색해서 확인해야 한다.
검색 결과가 명확하지 않으면 무조건 '불가능'으로 판단한다."""},
                {"role": "user", "content": f"""
'{word}' 단어를 네이버 국어사전에서 검색해줘.

검증 절차:
1. 네이버 국어사전에서 '{word}' 검색
2. 표제어로 등재되어 있는지 확인
3. 검색 결과가 없거나 애매하면 '불가능'

출력 형식:
결과: 가능 또는 불가능
근거: 검색 결과 요약

중요: 추측하지 말고 반드시 실제 검색 결과를 기반으로 판단할 것."""}
            ],
            temperature=0,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        first_line = result_text.split("\n")[0].lower()
        is_valid = "결과:" in first_line and "가능" in first_line and "불가능" not in first_line
        
        if "근거:" in result_text:
            reason = result_text.split("근거:")[-1].strip()
        else:
            reason = result_text
        
        uncertain_keywords = ["추정", "것으로 보임", "아닐 수도", "확실하지 않", "검색 결과가 없"]
        if any(keyword in result_text for keyword in uncertain_keywords):
            is_valid = False
            reason = f"불확실한 검증 결과: {reason[:100]}"
        
        if is_valid:
            st.session_state.verified_words.add(word)
        
        return is_valid, reason
        
    except Exception as e:
        return False, f"검증 실패: {str(e)[:50]}"

def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 4. UI 레이아웃 ---
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
    
    st.divider()
    st.caption(f"✅ 검증된 단어: {len(st.session_state.verified_words)}개")
    st.caption(f"🎮 현재 턴: {'AI' if st.session_state.is_ai_turn else '사용자'}")

st.title("AI 끝말잇기")
st.markdown("사전 검증 기능이 강화된 AI 대결!")

status_area = st.empty()
if not st.session_state.game_over:
    with status_area.container():
        cols = st.columns([4, 1])
        cols[0].progress(max(0, st.session_state.remaining_time / 30))
        cols[1].write(f"⏳ **{st.session_state.remaining_time}초**")

chat_placeholder = st.container(height=450)
with chat_placeholder:
    if not st.session_state.word_list:
        st.info("단어를 입력하여 게임을 시작하세요.")
    
    for i, word in enumerate(st.session_state.word_list):
        role = "user" if i % 2 == 0 else "assistant"
        st.chat_message(role).write(word)

error_area = st.empty()
if st.session_state.error_msg:
    error_area.warning(st.session_state.error_msg)

# --- 5. AI 턴 처리 ---
def process_ai_turn(user_word):
    """AI 턴을 처리하는 함수"""
    valid_starts_for_ai = get_valid_starts(user_word[-1])
    prompt = (
        f"한국어 끝말잇기 게임 중이야. 규칙은 다음과 같아.\n"
        f"1. 사용자가 방금 입력한 단어: '{user_word}' (검증 완료)\n"
        f"2. 다음 글자 중 하나로 시작하는 한국어 명사를 대답해: {', '.join(valid_starts_for_ai)}\n"
        f"   두음법칙 예시:\n"
        f"   - '냥'→'양', '녀'→'여', '뇨'→'요', '뉴'→'유', '니'→'이'\n"
        f"   - '랴'→'야', '려'→'여', '례'→'예', '료'→'요', '류'→'유', '리'→'이'\n"
        f"   - '라'→'나', '래'→'내', '로'→'노', '루'→'누', '르'→'느'\n"
        f"3. 반드시 네이버 국어사전에 등재된 표제어만 사용해.\n"
        f"4. 만약 단어를 찾지 못하겠다면 'I_LOSE'라고 답해.\n"
        f"5. 이미 사용된 단어들 (절대 재사용 금지): {st.session_state.word_list}\n"
        f"단어만 말하고 다른 설명은 하지 마."
    )

    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 끝말잇기 전문가야. 항상 사전에 등재된 단어만 사용해."},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.7
        )
        
        res_text = ""
        with chat_placeholder:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        res_text += chunk.choices[0].delta.content
                        message_placeholder.write(res_text + "▌")
                message_placeholder.write(res_text)
        
        res_text = res_text.strip()

        # AI 답변 검증
        if res_text == "I_LOSE":
            st.session_state.error_msg = "🎉 AI가 단어를 찾지 못해 패배를 선언했습니다!"
            st.session_state.game_over = True
            return
        
        if res_text in st.session_state.word_list:
            st.session_state.error_msg = f"🎉 AI가 중복된 단어 '{res_text}'를 말해서 패배했습니다!"
            st.session_state.game_over = True
            return
        
        # AI 시작 글자 검증
        expected_start = user_word[-1]
        valid_ai_starts = get_valid_starts(expected_start)
        
        if res_text[0] not in valid_ai_starts:
            st.session_state.error_msg = f"🎉 AI가 잘못된 시작 글자로 시작해서 패배했습니다!"
            st.session_state.game_over = True
            return
        
        # AI 단어 사전 검증
        with st.spinner("🔍 AI 단어 검증 중..."):
            ai_valid, ai_reason = verify_word_with_search(res_text)
            
            if not ai_valid:
                st.session_state.error_msg = f"🎉 AI가 사전에 없는 단어 '{res_text}'를 말해서 패배했습니다!"
                st.session_state.game_over = True
                return
        
        # AI 단어 추가 및 턴 종료
        st.session_state.word_list.append(res_text)
        st.session_state.remaining_time = 30
        st.session_state.error_msg = ""
        st.session_state.is_ai_turn = False
        
    except Exception as e:
        st.session_state.error_msg = f"AI 오류: {e}"
        st.session_state.game_over = True

# --- 6. 메인 로직 ---
if not st.session_state.game_over:
    # AI 턴인 경우
    if st.session_state.is_ai_turn and st.session_state.current_user_word:
        process_ai_turn(st.session_state.current_user_word)
        st.session_state.current_user_word = None
        st.rerun()
    
    # 사용자 입력 (AI 턴이 아닐 때만)
    user_input = st.chat_input("단어를 입력하세요...", disabled=st.session_state.is_ai_turn)

    if user_input and not st.session_state.is_ai_turn:
        user_input = user_input.strip()
        last_word = st.session_state.word_list[-1] if st.session_state.word_list else None
        valid_starts = get_valid_starts(last_word[-1]) if last_word else []

        # 기본 검증
        if user_input in st.session_state.word_list:
            st.session_state.error_msg = f"❌ '{user_input}'은(는) 이미 사용되었습니다!"
            st.rerun()
        elif last_word and (user_input[0] not in valid_starts):
            st.session_state.error_msg = f"❌ '{'/'.join(valid_starts)}'(으)로 시작해야 합니다!"
            st.rerun()
        else:
            # 사용자 단어 검증
            with st.spinner("🔍 단어 검증 중..."):
                is_valid, reason = verify_word_with_search(user_input)
                
                if not is_valid:
                    st.session_state.error_msg = f"❌ '{user_input}'은(는) 사전에 없는 단어입니다. ({reason})"
                    st.rerun()
            
            # 검증 통과 - 사용자 단어 추가 및 AI 턴으로 전환
            st.session_state.word_list.append(user_input)
            st.session_state.current_user_word = user_input
            st.session_state.error_msg = ""
            st.session_state.is_ai_turn = True
            st.rerun()

    # 타이머 (사용자 턴일 때만)
    if st.session_state.word_list and not st.session_state.is_ai_turn:
        time.sleep(1)
        st.session_state.remaining_time -= 1
        if st.session_state.remaining_time <= 0:
            st.session_state.game_over = True
        st.rerun()

# --- 7. 게임 종료 ---
else:
    status_area.empty()
    st.error("🎮 GAME OVER")
    score = len(st.session_state.word_list)
    st.markdown(f"### 최종 점수: {score} 단어")
    
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