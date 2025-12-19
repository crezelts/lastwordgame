import os, time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# --- 1. 설정 및 초기화 ---
st.set_page_config(page_title="순우리말 AI 끝말잇기", page_icon="🇰🇷", layout="centered")
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

# --- 2. 두음법칙 로직 ---
def get_valid_starts(last_char):
    starts = [last_char]
    code = ord(last_char)
    if 0xAC00 <= code <= 0xD7A3:
        char_code = code - 0xAC00
        cho = char_code // (21 * 28)
        jung = (char_code % (21 * 28)) // 28
        jong = char_code % 28
        if cho == 5 and jung in [2, 4, 8, 12, 13, 20]:
            starts.append(chr(0xAC00 + (11 * 21 * 28) + (jung * 28) + jong))
        elif cho == 5 and jung in [0, 5, 11, 18, 1, 10]:
            starts.append(chr(0xAC00 + (2 * 21 * 28) + (jung * 28) + jong))
        elif cho == 2 and jung in [4, 12, 13, 20]:
            starts.append(chr(0xAC00 + (11 * 21 * 28) + (jung * 28) + jong))
    return list(set(starts))

def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 3. UI 레이아웃 고정 ---
st.title("🇰🇷 AI 순우리말 끝말잇기")
st.markdown("사전 없이 AI와 직접 대결하세요! **외래어(닥터, 컴퓨터 등)**는 금지됩니다.")

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
    if not st.session_state.word_list:
        st.info("단어를 입력하여 게임을 시작하세요.")
    for i, word in enumerate(st.session_state.word_list):
        role = "user" if i % 2 == 0 else "assistant"
        st.chat_message(role).write(word)

# 에러 메시지 영역
error_area = st.empty()
if st.session_state.error_msg:
    error_area.warning(st.session_state.error_msg)

# --- 4. 메인 로직 ---
if not st.session_state.game_over:
    user_input = st.chat_input("단어를 입력하세요...")

    if user_input:
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
            # AI에게 단어 유효성 검사 및 다음 단어 요청 (사전 파일 대체)
            with chat_placeholder:
                with st.chat_message("assistant"):
                    msg_placeholder = st.empty()
                    ai_response = ""
                    
                    prompt = (
                        f"한국어 끝말잇기 게임 중이야. 규칙은 다음과 같아.\n"
                        f"1. 사용자가 방금 입력한 단어: '{user_input}'\n"
                        f"2. 규칙: 이 단어가 실제로 존재하는 한국어 명사인지, 그리고 외래어(Doctor, 컴퓨터 등)가 아닌지 판단해.\n"
                        f"3. 만약 부적절하다면 'INVALID:이유'라고 답해.\n"
                        f"4. 적절하다면, 사용자의 마지막 글자 '{user_input[-1]}' (두음법칙 허용: {valid_starts})로 시작하는 한국어 명사 하나만 대답해.\n"
                        f"5. 만약 네가 단어를 찾지 못하겠다면 'I_LOSE'라고 답해.\n"
                        f"6. 이미 사용된 단어들: {st.session_state.word_list}\n"
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
                            st.rerun()
                        elif res_text == "I_LOSE":
                            st.session_state.error_msg = "🎉 AI가 단어를 찾지 못해 패배를 선언했습니다!"
                            st.session_state.game_over = True
                            st.rerun()
                        else:
                            # 유효한 진행
                            st.session_state.error_msg = "" # 올바르면 에러 메시지 삭제
                            st.session_state.word_list.append(user_input)
                            st.session_state.word_list.append(res_text)
                            st.session_state.remaining_time = 30
                            st.rerun()
                    except Exception as e:
                        st.error(f"AI 오류: {e}")

    # 타이머
    if st.session_state.word_list and not st.session_state.game_over:
        time.sleep(1)
        st.session_state.remaining_time -= 1
        if st.session_state.remaining_time <= 0:
            st.session_state.game_over = True
        st.rerun()

# --- 5. 게임 종료 ---
else:
    status_area.empty()
    st.error("🎮 GAME OVER")
    st.markdown(f"### 최종 점수: {len(st.session_state.word_list)} 단어")
    if st.button("다시 시작하기", use_container_width=True):
        reset_game()