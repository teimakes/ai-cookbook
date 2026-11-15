# AI Cookbook

AI 모델과 도구를 사용한 실습 코드, 실험 설정, 실행 결과를 주제별로 정리한다. 각 실습은 자기 폴더에서 환경을 설치하고 실행한다.

## 실습 목록

| 주제 | 실습 | 사용 도구 | 평가·측정 범위 |
| --- | --- | --- | --- |
| 모델 평가 | [모델 응답 평가](evaluation/response-evaluation/README.md) | Mistral API, DeepEval | IFEval 지시 준수·한국어 전용 응답 평가, system 지시·prefix 적용 전후 비교 |
| 모델 평가 | [LLM 채점의 답변 순서 평가](evaluation/openai-eval/README.md) | OpenAI Responses API | 20문항·40판정 예비 실험 완료. 기준 판정 일치율·선택 변경률 비교 |
| 추론 성능 | [추론 소프트웨어와 성능 측정](inference-experiments/software-benchmarking/README.md) | Transformers, vLLM | 직접 실행과 HTTP 서버의 처리량·응답시간 측정 |

실습별 README에서 실행 조건, 비용 발생 여부, 확인된 범위와 결과의 한계를 확인한다. 모델 응답 평가는 답변이 지시와 언어 조건을 따르는지 측정하고, 추론 성능 측정은 실행 속도와 처리량을 다룬다.

## 저장소 구조

현재 문서화된 실습의 주요 파일은 다음과 같다.

```text
evaluation/
├── response-evaluation/
│   ├── README.md
│   ├── requirements.txt
│   ├── generate.ipynb
│   ├── data/
│   └── results/
└── openai-eval/
    ├── README.md
    ├── requirements.txt
    ├── evaluate.ipynb
    ├── data/
    └── results/
inference-experiments/
└── software-benchmarking/
    ├── README.md
    ├── requirements.txt
    ├── h100.ipynb
    ├── b300.ipynb
    ├── transformers_baseline.py
    └── vllm_baseline.py
```

실습은 제공사 이름보다 주제를 기준으로 분류한다. 사용 모델과 평가·측정 방법은 각 실습의 README에서 설명한다.

## 실행 방법

실습 폴더로 이동한 뒤 해당 README의 설치·실행 절차를 따른다. 의존성은 각 실습의 `requirements.txt`에서 확인한다.

모델 응답 평가 노트북은 가상환경을 활성화한 뒤 다음과 같이 연다.

```shell
cd evaluation/response-evaluation
python -m pip install -r requirements.txt
python -m jupyterlab generate.ipynb
```

실습 폴더의 `.env`에 `MISTRAL_API_STUDIO`를 설정하고, 설치에 사용한 가상환경의 Python 커널을 선택한다. `.env`, 가상환경, Python 캐시는 루트 `.gitignore`에서 제외한다.

응답 생성 셀을 실행하면 Mistral API를 호출하며 비용이 발생할 수 있다. 저장된 결과만 확인하려면 [응답 평가 실행 안내](evaluation/response-evaluation/README.md)의 시각화 절차를 따른다. 저장된 그래프는 README에서도 볼 수 있다.

## 문서와 공개 자료

실행 코드, 평가 문항, 응답과 평가 결과는 해당 실습 폴더에 둔다. 실습별 README에서 평가 방법, 실행 절차와 결과 해석 범위를 설명한다.

설명과 결과 해석은 [블로그](https://teimakes.github.io/)에, 학습 목적별 자료 링크는 [Free AI Campus](https://github.com/teimakes/free-ai-campus)에 정리할 수 있다.

[실습 추가 및 관리 방법](CONTRIBUTING.md)
