# Gemini API와 RAG 평가

## Gemini API
Gemini는 Google이 개발한 멀티모달 대규모 언어 모델 제품군이다. 텍스트, 이미지,
오디오, 코드를 처리할 수 있다. Google AI Studio에서 API 키를 발급받아 사용하며,
대표 모델로는 빠르고 저렴한 gemini-1.5-flash와 고성능의 gemini-1.5-pro가 있다.
텍스트 임베딩에는 text-embedding-004 모델을 사용한다.

## RAGAS 프레임워크
RAGAS(Retrieval-Augmented Generation Assessment)는 RAG 파이프라인을 자동으로
평가하기 위한 오픈소스 프레임워크다. 사람이 일일이 채점하지 않고 LLM을 심판으로
사용(LLM-as-a-judge)하여 평가 지표를 계산하는 것이 특징이다.

## RAGAS 핵심 지표
RAGAS의 대표적인 평가 지표는 다음과 같다.
- Faithfulness(충실성): 생성된 답변이 검색된 문맥에 의해 뒷받침되는 정도. 환각이
  적을수록 높다.
- Answer Relevancy(답변 관련성): 답변이 질문에 얼마나 직접적으로 부합하는지를 측정한다.
- Context Precision(문맥 정밀도): 검색된 문맥 중 실제로 정답에 유용한 부분의 비율이다.
- Context Recall(문맥 재현율): 정답을 구성하는 데 필요한 정보가 검색된 문맥에
  충분히 포함되었는지를 측정한다.

이 지표들은 모두 0에서 1 사이의 값을 가지며, 1에 가까울수록 좋다. Faithfulness와
Answer Relevancy는 생성(Generation) 품질을, Context Precision과 Context Recall은
검색(Retrieval) 품질을 진단하는 데 사용된다.
