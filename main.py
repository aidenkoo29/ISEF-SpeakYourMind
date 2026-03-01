import streamlit as st
import pandas as pd
import os
import json
import time
from openai import OpenAI
import requests
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context(user_aac_selections, counterpart_utterance):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
       {"role": "system", "content": "You are a helpful assistant."},
       {"role": "user", "content": f"""Your role is to inference the time/place/occasion of given conversation. Write as detailed as possible.
I'll provide you current selected cards.
I'll also provide you user history of AAC selections. In a single conversation, the user selects a few cards to make their sentence.

user AAC selections = {user_aac_selections}
counterpart utterance = {counterpart_utterance}

Give in the following format (Do not inlcude other words):
```json
{{
   "time": "XXX",
   "place": "XXX",
   "occasion": "XXX(Write longly detailed)"
}}
```"""}
   ]
)
    print(completion.choices[0].message.content)
    extracted_data = json.loads(completion.choices[0].message.content.split('```')[1].replace('json', ''))
    ans_time = extracted_data.get("time", "")
    ans_place = extracted_data.get("place", "")
    ans_occasion = extracted_data.get("occasion", "")
    return ans_time, ans_place, ans_occasion


def get_suggestion(aac_word_set, user_aac_selections, counterpart_utterance, ans_time, ans_place, ans_occasion):

    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
   {"role": "developer", "content": "You are a helpful assistant."},
   {"role": "user", "content": f"""I will provide you with a scenario, where one user is using AAC to communicate, and the Counterpart is using speech to communicate.
    With the Context provided, suggest a word from the AAC Library that would be most fitting in the following situation.
   The Word Library will be provided, YOU MUST SUGGEST WORD FROM THE LIBRARY
   Additionally, I will provide the AAC words used by the user.
   
   AAC Library = {aac_word_set}
   user AAC selections = {user_aac_selections}
   counterpart utterance = {counterpart_utterance}

   time = {ans_time}
   place = {ans_place}
   occasion = {ans_occasion}

   Give in the following format (Do not inlcude other words):
   ```json
   {{
       "words": ["word1", "word2", "word3", "word4", "word5"],
       "categories": ["category1", category2", "category3", "category4", "category5"]
   }}
   ```
    
    """}
    ]
    )
    print(completion.choices[0].message.content)
    suggestion_json = completion.choices[0].message.content.split('```')[1].replace('json', '')
    suggestion_data = json.loads(suggestion_json)
    return list(zip(suggestion_data['categories'], suggestion_data['words']))

def get_augmentation(aac_word_set, conversation):
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
    {"role": "developer", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"""I will provide you with a conversation, where one user is using AAC to communicate, and the Counterpart is using speech to communicate.
    Suggest a new word that is not currently in the library. The Word Library will be provided.
    Produce 3 words with the category and word, that is the most optimal for the situation.

    AAC Library = {aac_word_set}
    conversation = {conversation}

    Give in the following format (Do not include other words):
    ```json
    {{
        "words": ["word1", "word2", "word3"],
        "categories": ["category1", category2", "category3"]
    }}
    ```

"""}
]
)
    print(completion.choices[0].message.content)
    suggestion_json = (completion.choices[0].message.content.split('```')[1].replace('json', ''))
    return json.loads(suggestion_json)


# -----------------------------------------------------------------------------

# 와이드 레이아웃 설정
st.set_page_config(layout="wide")
st.title('무발화자폐인을 위한 개인맞춤 AAC')

# CSV 로딩
aac_library = pd.read_csv('./aac_library.csv')
categories = sorted(aac_library['category'].unique())

# 세션 상태 초기화
if 'suggestion' not in st.session_state:
    st.session_state.suggestion = []
if 'selection' not in st.session_state:
    st.session_state.selection = []
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcription' not in st.session_state:
    st.session_state.transcription = ''
if 'conversations' not in st.session_state:
    st.session_state.conversation = []

# 카드 함수 정의
def card(category, word, key_prefix='card'):
    image_path = f'./aac_images/{category}/{word}.png'
    with st.container():
        if st.button(f"🖼️ {word}", key=f"{key_prefix}-{category}-{word}"):
            if (category, word) not in st.session_state.selection:
                st.session_state.selection.append((category, word))
                st.rerun()  # 즉시 반영
        if os.path.exists(image_path):
            st.image(image_path, width=100)
        else:
            st.text("이미지 없음")
        st.caption(word)


# 선택된 카드 (상단)
st.subheader("선택된 카드")

col1, col2 = st.columns([8, 2])

with col1:
    if st.session_state.selection:
        cols = st.columns(len(st.session_state.selection))
        for i, (category, word) in enumerate(st.session_state.selection):
            with cols[i]:
                card(category, word, key_prefix='selected')
    else:
        st.info("선택된 카드가 없습니다.")

with col2:
    # 녹음 토글 버튼
    if st.session_state.recording:
        if st.button("🔴 녹음중지"):
            st.session_state.recording = False
            with st.spinner('녹음 분석 중입니다'):
                time.sleep(3)
            
            user_aac_selections = [word for _, word in st.session_state.selection]
            counterpart_utterance = "맛있어?"

            st.session_state.conversation.append('Me'+str(user_aac_selections))
            st.session_state.conversation.append('Counterpart'+counterpart_utterance)

            # Step 2: Get context (time, place, occasion)
            ans_time, ans_place, ans_occasion = get_context(user_aac_selections, counterpart_utterance)
            aac_word_set = aac_library.to_dict(orient='records')
            st.session_state.suggestion = get_suggestion(aac_word_set, user_aac_selections, counterpart_utterance, ans_time, ans_place, ans_occasion)

            # print result
            print('-'*30)
            print('time: ', ans_time)
            print('place: ', ans_place)
            print('occasion: ', ans_occasion)

            st.session_state.selection = []
            st.rerun()  # 즉시 반영
    else:
        if st.button("🟢 말하기"):
            st.session_state.recording = True
            st.rerun()  # 즉시 반영

    # 생성 버튼
    if st.button("➕ 카드 추가하기"):
        aac_word_set = aac_library.to_dict(orient='records')
        new_cards = get_augmentation(aac_word_set, st.session_state.conversation)

        st.write('오늘 있었던 대화를 기반으로 AAC에 새로운 카드를 추가하겠습니다')
        for i in range(3):
            st.write(new_cards['words'][i], '-', new_cards['categories'][i])

        
        # new_cards 는 {"words":[…], "categories":[…]} 형태
        words     = new_cards.get("words", [])
        categories = new_cards.get("categories", [])

        if not words:
            st.warning("추천할 새 카드가 없습니다.")
        else:
            for cat, word in zip(categories, words):
                # 1) 라이브러리에 이미 존재하는지 확인
                already_there = (
                    (aac_library["category"] == cat) &
                    (aac_library["word"] == word)
                ).any()

                if not already_there:
                    # 2-A) CSV(DataFrame) 에 행 추가
                    aac_library.loc[len(aac_library)] = {"category": cat, "word": word}

                    # 2-B) 이미지 폴더/파일 준비
                    img_dir  = Path(f"./aac_images/{cat}")
                    img_dir.mkdir(parents=True, exist_ok=True)
                    img_path = img_dir / f"{word}.png"

                    if not img_path.exists():
                        # 3) DALL·E 로 이미지 생성 후 저장
                        prompt = f"White background. Draw '{word}({cat})' iconic pictogram 2D illustration that can be used as Alternative or augmentative communication (AAC)."
                        result = client.images.generate(
                            model="dall-e-3",
                            prompt=prompt,
                            size="1024x1024",
                        )
                        image_url = result.data[0].url
                        try:
                            img_data = requests.get(image_url, timeout=10).content
                            with open(img_path, "wb") as f:
                                f.write(img_data)
                        except Exception as e:
                            st.error(f"이미지 다운로드 실패: {e}")

            # 4) CSV 파일 덮어쓰기(추가 사항 저장)
            aac_library.to_csv("./aac_library.csv", index=False)

            st.success("새로운 카드가 라이브러리에 추가되었습니다!")
            st.rerun()

# 제안된 카드
if st.session_state.suggestion:
    st.subheader("제안된 카드")
    cols = st.columns(len(st.session_state.suggestion))
    for i, (category, word) in enumerate(st.session_state.suggestion):
        with cols[i]:
            card(category, word, key_prefix='suggest')

# 카테고리별 라이브러리 카드
tabs = st.tabs(categories)
for tab, category in zip(tabs, categories):
    with tab:
        st.markdown(f"### {category}")
        category_df = aac_library[aac_library['category'] == category]
        cols = st.columns(5)
        for i, row in category_df.iterrows():
            with cols[i % 5]:
                card(row['category'], row['word'], key_prefix='library')
