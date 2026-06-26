import os
import json
import pickle

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(BASE_DIR, "data", "corpus.txt")
MODEL_PATH = os.path.join(BASE_DIR, "artifacts", "next_word_model.keras")
TOKENIZER_PATH = os.path.join(BASE_DIR, "artifacts", "tokenizer.pkl")
META_PATH = os.path.join(BASE_DIR, "artifacts", "meta.json")

def load_corpus(path=CORPUS_PATH):
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def build_tokenizer(lines):
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(lines)
    return tokenizer

def make_sequences(lines, tokenizer):
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

def build_model(vocab_size, max_len, embedding_dim=64, lstm_units=128):
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

def save_artifacts(model, tokenizer, max_len):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    with open(TOKENIZER_PATH, "wb") as f:
        pickle.dump(tokenizer, f)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump({"max_len": max_len}, f, ensure_ascii=False)

def load_artifacts():
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

def predict_next_word(model, tokenizer, max_len, text, temperature=1.0):
    token_list = tokenizer.texts_to_sequences([text])[0]
    token_list = pad_sequences([token_list], maxlen=max_len - 1, padding="pre")

    preds = model.predict(token_list, verbose=0)[0].astype("float64")

    preds = np.log(preds + 1e-9) / max(temperature, 1e-3)
    preds = np.exp(preds)
    preds = preds / np.sum(preds)
    next_index = np.random.choice(len(preds), p=preds)

    return tokenizer.index_word.get(next_index, "")

SENTENCE_ENDINGS = ("다", "요", "까", "죠", "네", "군요", "세요", "에요", "예요")

def _is_sentence_end(word):
    return word.endswith(SENTENCE_ENDINGS)

def generate_sentence(model, tokenizer, max_len, seed_text,
                      max_words=20, temperature=0.8):
    result = seed_text.strip()
    last_word = None
    repeat = 0

    for _ in range(max_words):
        next_word = predict_next_word(model, tokenizer, max_len, result, temperature)
        if not next_word or next_word == "<OOV>":
            break
        if next_word == last_word:
            repeat += 1
            if repeat >= 2:        
                break
        else:
            repeat = 0
        result += " " + next_word
        last_word = next_word
        if _is_sentence_end(next_word):   
            break

    answer = result[len(seed_text.strip()):].strip()
    return answer if answer else result
