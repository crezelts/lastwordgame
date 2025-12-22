# 🇰🇷 AI 끝말잇기 게임

OpenAI GPT-4o-mini를 활용한 한국어 끝말잇기 게임입니다. 사전 파일 없이 AI가 직접 단어의 유효성을 판단하고 게임을 진행합니다.

## ✨ 주요 기능

- 🤖 **AI 대결**: GPT-4o-mini와 실시간 끝말잇기 대결
- ⏱️ **30초 타이머**: 긴장감 넘치는 시간 제한 게임
- 📝 **두음법칙 지원**: 냥→양, 녀→여 등 한국어 두음법칙 자동 적용
- 🏆 **랭킹 시스템**: 최고 점수 상위 10명 기록 저장
- 💬 **채팅 UI**: 직관적인 채팅 형식의 게임 인터페이스
- ✅ **중복 검사**: 이미 사용된 단어 자동 체크

## 🎮 게임 규칙

1. 사용자가 먼저 단어를 입력합니다
2. AI가 단어의 유효성을 검증하고 다음 단어를 제시합니다
3. 30초 안에 단어를 입력하지 못하면 게임 오버
4. 중복된 단어를 사용하면 패배
5. 두음법칙이 적용됩니다 (예: '냥'으로 끝나면 '양'으로 시작 가능)

## 🚀 설치 및 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/ai-word-chain-game.git
cd ai-word-chain-game
```

### 2. 가상환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 OpenAI API 키를 입력합니다:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

> 💡 OpenAI API 키는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 발급받을 수 있습니다.

### 5. 게임 실행

```bash
streamlit run main.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 게임을 플레이할 수 있습니다.

## 📁 프로젝트 구조

```
ai-word-chain-game/
├── main.py              # 메인 애플리케이션 파일
├── requirements.txt     # Python 패키지 의존성
├── .env                 # 환경 변수 (직접 생성 필요)
├── rank.json           # 랭킹 데이터 저장 파일 (자동 생성)
├── lastword.txt        # AI 프롬프트 규칙 문서
└── README.md           # 프로젝트 설명서
```

## 🎯 두음법칙 적용 예시

| 끝나는 글자 | 시작 가능한 글자 |
|------------|-----------------|
| 냥 | 냥, 양 |
| 녀 | 녀, 여 |
| 뇨 | 뇨, 요 |
| 뉴 | 뉴, 유 |
| 니 | 니, 이 |
| 랴 | 랴, 야 |
| 려 | 려, 여 |
| 료 | 료, 요 |
| 류 | 류, 유 |
| 리 | 리, 이 |
| 라 | 라, 나 |
| 래 | 래, 내 |

## 🛠️ 기술 스택

- **Frontend/UI**: Streamlit
- **AI Model**: OpenAI GPT-4o-mini
- **Language**: Python 3.8+
- **Data Storage**: JSON 파일

## 📋 requirements.txt

```
streamlit
openai
python-dotenv
```

## 🎮 게임 플레이 팁

1. **시간 관리**: 30초 제한이 있으니 빠르게 생각하세요
2. **어려운 글자로 끝내기**: 'ㅋ', 'ㅌ', 'ㅍ' 등으로 끝나는 단어를 선택하면 AI가 어려워합니다
3. **두음법칙 활용**: AI도 두음법칙을 사용하니 '녀', '료' 등으로 끝나는 단어도 괜찮습니다
4. **외래어 활용**: 외래어도 허용되므로 다양한 단어를 시도해보세요

## 🏆 랭킹 시스템

- 게임 종료 시 자동으로 점수가 계산됩니다 (사용한 단어 개수)
- 상위 10명의 기록이 저장됩니다
- 사이드바에서 명예의 전당을 확인할 수 있습니다

## ⚠️ 문제 해결

### API 키 오류
```
Error: OpenAI API key not found
```
→ `.env` 파일에 올바른 API 키가 설정되어 있는지 확인하세요.

### rank.json 오류
```
JSONDecodeError: Expecting value
```
→ `rank.json` 파일을 삭제하고 다시 실행하면 자동으로 생성됩니다.

### Streamlit 실행 오류
```
streamlit: command not found
```
→ 가상환경이 활성화되어 있는지 확인하고, `pip install streamlit`을 다시 실행하세요.

## 🤝 기여하기

버그 리포트, 기능 제안, Pull Request는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 문의

프로젝트에 대한 문의사항이 있으시면 Issue를 생성해주세요.

---

**Enjoy the game! 🎮🇰🇷**
