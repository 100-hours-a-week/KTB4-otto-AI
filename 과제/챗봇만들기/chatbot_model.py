"""
한국어 챗봇 - 공용 모듈
==========================
- 코퍼스 로딩 / 토크나이저 생성
- 다음 단어 예측 LSTM 모델 정의 (과제 5-1)
- 모델을 반복 호출하여 완전한 문장을 생성하는 함수 (과제 5-2)

train.py 와 app.py(FastAPI) 가 이 모듈을 함께 사용한다.
"""

import os
import json
import pickle

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout

# 산출물 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(BASE_DIR, "data", "corpus.txt")
MODEL_PATH = os.path.join(BASE_DIR, "artifacts", "next_word_model.keras")
TOKENIZER_PATH = os.path.join(BASE_DIR, "artifacts", "tokenizer.pkl")
META_PATH = os.path.join(BASE_DIR, "artifacts", "meta.json")


# ---------------------------------------------------------------------------
# 1. 데이터 준비
# ---------------------------------------------------------------------------
def load_corpus(path=CORPUS_PATH):
    """코퍼스 파일을 읽어 문장 리스트로 반환."""
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def build_tokenizer(lines):
    """문장 리스트로 단어 토크나이저를 생성한다 (OOV 토큰 포함)."""
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(lines)
    return tokenizer


def make_sequences(lines, tokenizer):
    """
    각 문장을 n-gram 형태의 입력 시퀀스로 변환한다.
    예) "오늘 날씨가 좋네요" ->
        [오늘, 날씨가]
        [오늘, 날씨가, 좋네요]
    마지막 토큰이 정답(label), 앞부분이 입력(feature)이 된다.
    """
    sequences = []
    for line in lines:
        token_list = tokenizer.texts_to_sequences([line])[0]
        for i in range(1, len(token_list)):
            sequences.append(token_list[: i + 1])

    max_len = max(len(s) for s in sequences)
    sequences = np.array(pad_sequences(sequences, maxlen=max_len, padding="pre"))

    X = sequences[:, :-1]
    y = sequences[:, -1]
    return X, y, max_len


# ---------------------------------------------------------------------------
# 2. 모델 정의 (과제 5-1: 다음 단어 생성 모델)
# ---------------------------------------------------------------------------
def build_model(vocab_size, max_len, embedding_dim=64, lstm_units=128):
    """다음 단어를 예측하는 LSTM 언어 모델."""
    model = Sequential([
        Embedding(vocab_size, embedding_dim, input_length=max_len - 1),
        LSTM(lstm_units, return_sequences=True),
        Dropout(0.2),
        LSTM(lstm_units),
        Dense(lstm_units, activation="relu"),
        Dense(vocab_size, activation="softmax"),
    ])
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer="adam",
        metrics=["accuracy"],
    )
    return model


# ---------------------------------------------------------------------------
# 3. 저장 / 로딩
# ---------------------------------------------------------------------------
def save_artifacts(model, tokenizer, max_len):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    with open(TOKENIZER_PATH, "wb") as f:
        pickle.dump(tokenizer, f)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump({"max_len": max_len}, f, ensure_ascii=False)


def load_artifacts():
    """학습된 모델/토크나이저/메타데이터를 로딩한다."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "학습된 모델이 없습니다. 먼저 `python3 train.py` 를 실행하세요."
        )
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(TOKENIZER_PATH, "rb") as f:
        tokenizer = pickle.load(f)
    with open(META_PATH, encoding="utf-8") as f:
        max_len = json.load(f)["max_len"]
    return model, tokenizer, max_len


# ---------------------------------------------------------------------------
# 4. 다음 단어 예측 (과제 5-1)
# ---------------------------------------------------------------------------
def predict_next_word(model, tokenizer, max_len, text, temperature=1.0):
    """
    입력 문장(text) 다음에 올 단어 하나를 예측해 반환한다.
    temperature 로 무작위성을 조절한다 (낮을수록 보수적).
    """
    token_list = tokenizer.texts_to_sequences([text])[0]
    token_list = pad_sequences([token_list], maxlen=max_len - 1, padding="pre")

    preds = model.predict(token_list, verbose=0)[0].astype("float64")

    # temperature 샘플링
    preds = np.log(preds + 1e-9) / max(temperature, 1e-3)
    preds = np.exp(preds)
    preds = preds / np.sum(preds)
    next_index = np.random.choice(len(preds), p=preds)

    return tokenizer.index_word.get(next_index, "")


# ---------------------------------------------------------------------------
# 5. 문장 생성 (과제 5-2: 모델을 반복 호출하여 완전한 문장 생성)
# ---------------------------------------------------------------------------
# 한국어 종결 어미 (이 어미로 끝나는 단어가 나오면 문장을 마친다)
SENTENCE_ENDINGS = ("다", "요", "까", "죠", "네", "군요", "세요", "에요", "예요")


def _is_sentence_end(word):
    return word.endswith(SENTENCE_ENDINGS)


def generate_sentence(model, tokenizer, max_len, seed_text,
                      max_words=20, temperature=0.8):
    """
    seed_text 를 시작으로 다음 단어 예측을 반복하여 문장을 완성한다.
    - 종결 어미로 끝나는 단어가 나오면 문장을 마친다.
    - 같은 단어가 연속 반복되면 멈춰서 무한 루프를 방지한다.
    """
    result = seed_text.strip()
    last_word = None
    repeat = 0

    for _ in range(max_words):
        next_word = predict_next_word(model, tokenizer, max_len, result, temperature)
        if not next_word or next_word == "<OOV>":
            break
        if next_word == last_word:
            repeat += 1
            if repeat >= 2:        # 같은 단어 3회 연속이면 종료
                break
        else:
            repeat = 0
        result += " " + next_word
        last_word = next_word
        if _is_sentence_end(next_word):   # 종결 어미면 문장 종료
            break

    # seed 를 제외한 생성 부분만 응답으로 반환
    answer = result[len(seed_text.strip()):].strip()
    return answer if answer else result
