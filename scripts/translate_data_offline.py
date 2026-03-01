from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
AAC_IMAGES_DIR = ROOT / "aac_images"
AAC_AUDIOS_DIR = ROOT / "aac_audios"

AAC_LIBRARY_PATH = DATA_DIR / "aac_library.csv"
ORIGINAL_AAC_LIBRARY_PATH = DATA_DIR / "original_aac_library.csv"
COMMUNITY_LIBRARY_PATH = DATA_DIR / "community_library.json"

CATEGORY_MAP = {
    "사람": "People",
    "감정": "Feelings",
    "음식": "Food",
    "장소": "Places",
    "행동": "Actions",
    "물건": "Objects",
    "질문": "Questions",
    "시간": "Time",
}

WORD_MAP = {
    "나": "I",
    "너": "You",
    "우리": "We",
    "엄마": "Mom",
    "아빠": "Dad",
    "형": "Older Brother",
    "누나": "Older Sister",
    "오빠": "Brother",
    "언니": "Sister",
    "동생": "Younger Sibling",
    "할머니": "Grandma",
    "할아버지": "Grandpa",
    "선생님": "Teacher",
    "친구": "Friend",
    "아기": "Baby",
    "의사": "Doctor",
    "간호사": "Nurse",
    "운전기사": "Driver",
    "경찰관": "Police Officer",
    "소방관": "Firefighter",
    "슬퍼요": "Sad",
    "화나요": "Angry",
    "무서워요": "Scared",
    "놀랐어요": "Surprised",
    "지루해요": "Bored",
    "피곤해요": "Tired",
    "긴장돼요": "Nervous",
    "불안해요": "Anxious",
    "행복해요": "Happy",
    "미안해요": "Sorry",
    "고마워요": "Thank You",
    "과자": "Snack",
    "빵": "Bread",
    "우유": "Milk",
    "물": "Water",
    "주스": "Juice",
    "사과": "Apple",
    "바나나": "Banana",
    "치킨": "Chicken",
    "피자": "Pizza",
    "햄버거": "Hamburger",
    "계란": "Egg",
    "아이스크림": "Ice Cream",
    "수박": "Watermelon",
    "초콜릿": "Chocolate",
    "집": "Home",
    "학교": "School",
    "화장실": "Bathroom",
    "병원": "Hospital",
    "마트": "Market",
    "놀이터": "Playground",
    "식당": "Restaurant",
    "교실": "Classroom",
    "운동장": "Field",
    "도서관": "Library",
    "방": "Room",
    "거실": "Living Room",
    "주방": "Kitchen",
    "공원": "Park",
    "수영장": "Swimming Pool",
    "동물원": "Zoo",
    "영화관": "Movie Theater",
    "교회": "Church",
    "버스정류장": "Bus Stop",
    "가요": "Go",
    "와요": "Come",
    "먹어요": "Eat",
    "마셔요": "Drink",
    "자요": "Sleep",
    "씻어요": "Wash",
    "놀아요": "Play",
    "일어나요": "Wake Up",
    "앉아요": "Sit",
    "일해요": "Work",
    "말해요": "Speak",
    "읽어요": "Read",
    "써요": "Write",
    "웃어요": "Smile",
    "울어요": "Cry",
    "줘요": "Give",
    "받아요": "Receive",
    "봐요": "Look",
    "만져요": "Touch",
    "기다려요": "Wait",
    "책": "Book",
    "연필": "Pencil",
    "지우개": "Eraser",
    "가방": "Bag",
    "옷": "Clothes",
    "신발": "Shoes",
    "장난감": "Toy",
    "공": "Ball",
    "휴대폰": "Phone",
    "컴퓨터": "Computer",
    "텔레비전": "Television",
    "컵": "Cup",
    "숟가락": "Spoon",
    "포크": "Fork",
    "수건": "Towel",
    "이불": "Blanket",
    "베개": "Pillow",
    "우산": "Umbrella",
    "시계": "Clock",
    "칫솔": "Toothbrush",
    "도와주세요": "Help Me",
    "주세요": "Please",
    "더 주세요": "More Please",
    "싫어요": "No",
    "좋아요": "Okay",
    "이거 해요": "Do This",
    "그만해요": "Stop",
    "같이 해요": "Together",
    "기다려 주세요": "Please Wait",
    "할래요": "I Want To",
    "안 할래요": "I Don't Want To",
    "오늘": "Today",
    "내일": "Tomorrow",
    "어제": "Yesterday",
    "지금": "Now",
    "나중에": "Later",
    "아침": "Morning",
    "점심": "Lunch",
    "저녁": "Evening",
    "밤": "Night",
    "새벽": "Dawn",
    "월요일": "Monday",
    "화요일": "Tuesday",
    "수요일": "Wednesday",
    "목요일": "Thursday",
    "금요일": "Friday",
    "토요일": "Saturday",
    "일요일": "Sunday",
    "주말": "Weekend",
    "시간이에요": "Time",
    "식사": "Meal",
    "학원": "Academy",
    "레슨": "Lesson",
    "식장": "Restaurant",
    "슬픔": "Sadness",
    "화": "Anger",
    "무서움": "Fear",
    "놀람": "Surprise",
    "지루함": "Boredom",
    "피곤": "Fatigue",
    "긴장": "Tension",
    "불안": "Anxiety",
    "행복": "Happiness",
    "미안": "Sorry",
    "감사": "Thanks",
    "닭고기": "Chicken",
    "슈퍼마켓": "Supermarket",
    "버스 정류장": "Bus Stop",
    "가다": "Go",
    "오다": "Come",
    "먹다": "Eat",
    "마시다": "Drink",
    "자다": "Sleep",
    "씻다": "Wash",
    "놀다": "Play",
    "일어나다": "Wake Up",
    "앉다": "Sit",
    "일하다": "Work",
    "말하다": "Speak",
    "읽다": "Read",
    "쓰다": "Write",
    "웃다": "Smile",
    "울다": "Cry",
    "주다": "Give",
    "받다": "Receive",
    "보다": "Look",
    "만지다": "Touch",
    "기다리다": "Wait",
    "도움": "Help",
    "더": "More",
    "싫어": "No",
    "좋아": "Okay",
    "이것을 하다": "Do This",
    "그만": "Stop",
    "함께": "Together",
    "하다": "Do",
    "안 하다": "Do Not",
    "시간": "Time",
    "음식": "Food",
    "물건": "Objects",
}


def map_text(text: str) -> str:
    if not text:
        return text
    return WORD_MAP.get(text, text)


def translate_csv(path: Path) -> None:
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    translated_rows = []
    for row in rows:
        translated_rows.append(
            {
                "category": CATEGORY_MAP.get(row["category"], row["category"]),
                "word": map_text(row["word"]),
                "search_term_arasaac": map_text(row.get("search_term_arasaac", "")),
            }
        )

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "word", "search_term_arasaac"])
        writer.writeheader()
        writer.writerows(translated_rows)


def rename_assets_from_library() -> None:
    with open(ORIGINAL_AAC_LIBRARY_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        src_cat = row["category"]
        src_word = row["word"]
        dst_cat = CATEGORY_MAP.get(src_cat, src_cat)
        dst_word = map_text(src_word)

        img_src = AAC_IMAGES_DIR / src_cat / f"{src_word}.png"
        img_dst = AAC_IMAGES_DIR / dst_cat / f"{dst_word}.png"
        audio_src = AAC_AUDIOS_DIR / src_cat / f"{src_word}.mp3"
        audio_dst = AAC_AUDIOS_DIR / dst_cat / f"{dst_word}.mp3"

        if img_src.exists():
            img_dst.parent.mkdir(parents=True, exist_ok=True)
            if not img_dst.exists():
                shutil.move(str(img_src), str(img_dst))

        if audio_src.exists():
            audio_dst.parent.mkdir(parents=True, exist_ok=True)
            if not audio_dst.exists():
                shutil.move(str(audio_src), str(audio_dst))


def translate_community() -> None:
    if not COMMUNITY_LIBRARY_PATH.exists():
        return

    cards = json.loads(COMMUNITY_LIBRARY_PATH.read_text(encoding="utf-8"))
    for card in cards:
        original_name = card.get("name", "")
        original_category = card.get("category", "")

        card["name"] = map_text(original_name)
        card["category"] = CATEGORY_MAP.get(original_category, original_category)
        card["tags"] = [map_text(tag) for tag in card.get("tags", [])]
        card["context_time"] = map_text(card.get("context_time", ""))
        card["context_place"] = map_text(card.get("context_place", ""))
        card["context_occasion"] = map_text(card.get("context_occasion", ""))

        # Keep paths aligned with translated categories/words.
        card["image"] = f"aac_images/{card['category']}/{card['name']}.png"
        card["audio"] = f"aac_audios/{card['category']}/{card['name']}.mp3"

    COMMUNITY_LIBRARY_PATH.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    rename_assets_from_library()
    translate_csv(AAC_LIBRARY_PATH)
    translate_csv(ORIGINAL_AAC_LIBRARY_PATH)
    translate_community()
    print("Offline translation migration complete.")


if __name__ == "__main__":
    main()
