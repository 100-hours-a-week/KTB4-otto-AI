"""
한국어 챗봇 학습 스크립트 (과제 5-1)
=====================================
코퍼스를 읽어 '다음 단어 예측' LSTM 모델을 학습하고 artifacts/ 에 저장한다.

실행:
    python3 train.py
"""

import chatbot_model as cm


def main(epochs=300):
    print("[1/4] 코퍼스 로딩...")
    lines = cm.load_corpus()
    print(f"      문장 수: {len(lines)}")

    print("[2/4] 토크나이저 생성 및 시퀀스 변환...")
    tokenizer = cm.build_tokenizer(lines)
    vocab_size = len(tokenizer.word_index) + 1
    X, y, max_len = cm.make_sequences(lines, tokenizer)
    print(f"      어휘 크기: {vocab_size}, 최대 길이: {max_len}, 학습 샘플: {len(X)}")

    print("[3/4] 모델 학습...")
    model = cm.build_model(vocab_size, max_len)
    model.summary()
    model.fit(X, y, epochs=epochs, verbose=2)

    print("[4/4] 모델/토크나이저 저장...")
    cm.save_artifacts(model, tokenizer, max_len)
    print(f"      저장 완료 -> {cm.MODEL_PATH}")

    # 간단한 생성 테스트
    print("\n=== 생성 테스트 ===")
    for seed in ["안녕하세요", "오늘 날씨가", "파이썬은", "딥러닝은"]:
        ans = cm.generate_sentence(model, tokenizer, max_len, seed, temperature=0.6)
        print(f"  입력: {seed}  ->  생성: {ans}")


if __name__ == "__main__":
    main()
