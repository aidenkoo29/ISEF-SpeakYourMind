# SpeakYourMind
- 제작: 구준한, 임채원

## 🧩 문제제기

무발화 자폐인은 의사소통의 어려움을 겪습니다.
유일한 해결책인 AAC(Augmentative and Alternative Communication) 보조도구들은 표현의 다양성이 부족하거나 사용의 불편함으로 상황에 맞는 대화를 자유로이 하기 어렵습니다.

---

## 💡 SpeakYourMind

**SpeakYourMind**는 대화 맥락 인식하여, 사용자가 말하고자 하는 의도를 예측하고
관련된 대화 카드를 추천해주는 **AI기반 AAC 앱**입니다.

* 사용자는 개인화된 **대화 카드**를 사용해 대화를 진행합니다.
* 비장애인의 음성 대화를 녹음하여 대화 맥락에 더욱 적합한 대화 카드를 추천할 수 있습니다.
* 매 대화마다 AI를 통하여 상황에 적절한 대화 카드를 추천받습니다.
* AI는 향후 필요할 법한 대화 카드를 파악하여 이미지심볼/음성오디오와 함께 새로운 카드를 생성합니다.

---

## ⚙️ 사용법 (Usage)

1. **모델 및 OpenAI API key 준비**
   `model/cc.ko.300.bin` 파일을 준비합니다.
   (FastText 한국어 임베딩 모델을 사용합니다.) 또한 OpenAI API Key를 준비하여 `app.py`에 등록해줍니다.

2. **서버 실행**
   ```bash
   uvicorn app:app --reload
   ```

3. **앱 실행**
   브라우저에서 `index.html` 파일을 열어 실행합니다.

---

### (Optional)

* 초기 카드 라이브러리를 커스텀할 수 있습니다. 커스텀을 원하시는 경우
  `original_aac_library.csv` 파일을 수정하세요.
  (카테고리와 단어를 추가하면 자동으로 UI에 반영됩니다.)

---

## 👩‍💻 개발환경

* Python 3.10+
* FastText (cc.ko.300.bin)
* Frontend: HTML, CSS, JavaScript
* Backend: FastAPI
