# EAGLE-3 draft model 학습

[실습 노트북](eagle3-training.ipynb)은 Qwen/Qwen3.8-27B를 target으로 고정하고 EAGLE-3 draft model을 학습한 뒤 vLLM에서 적용 전후를 비교한다.

## 별도 학습이 필요한 경우

모든 speculative decoding 방법에 학습이 필요한 것은 아니다. N-gram·Suffix는 추가 모델이 없고, 일반 draft model은 기존 소형 모델을 사용할 수 있다. EAGLE-3·DFlash는 target에 맞는 학습된 draft가 필요하지만 공개 가중치가 있으면 다시 학습하지 않아도 된다. Native MTP도 학습된 MTP 가중치를 포함한 target과 엔진 지원이 있으면 바로 사용할 수 있다.

vLLM 문서가 직접 연결하는 학습 도구는 [vllm-project/speculators](https://docs.vllm.ai/en/stable/features/speculative_decoding/speculators/)다. 이 실습은 [공식 학습 튜토리얼](https://docs.vllm.ai/projects/speculators/en/latest/user_guide/tutorials/train/)의 오프라인 EAGLE-3 절차를 사용한다. 작은 범용 LLM을 처음부터 사전학습하지 않고 target의 hidden state를 사용하는 draft를 학습한다.

## 환경 준비

- Linux, Python 3.11 이상, 각 GPU를 지원하는 PyTorch·CUDA가 필요하다.
- 한 서버의 H100 4개 또는 B300 1개를 사용한다. 노트북의 `HARDWARE`로 선택한다.
- 학습 환경과 vLLM 환경을 분리한다. 노트북에서는 학습 환경을 사용하고 `VLLM_PYTHON`에 vLLM 환경의 Python 절대 경로를 적는다.
- Speculators 학습 가이드는 vLLM 0.27.1 이상을 안내한다. 모델을 일반 서빙할 수 있다는 것만으로 hidden state 추출·EAGLE-3 학습까지 지원된다고 판단하지 않는다.
- CLI/API는 Speculators v0.9.0 소스를 기준으로 대조했다. 회사 GPU 환경에서 검증한 패키지 버전은 없으며, `requirements.txt`는 설치 항목 목록이다.
- `return_token_ids`, hidden state extraction, `ExampleHiddenStatesConnector`, EAGLE-3와 speculative decoding metric을 지원하는 vLLM 환경이 필요하다.

학습용 환경을 이 폴더에 준비한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Jupyter에서 이 환경의 Python 커널을 선택한다. vLLM 환경에는 학습 패키지를 설치하지 않는다. 노트북에는 GPU 패키지를 자동으로 교체하는 셀이 없다.

vLLM의 현재 CLI 표기는 `--disable-prefix-caching`, `--disable-chunked-prefill`이다. 설치 버전이 `--no-enable-prefix-caching`, `--no-enable-chunked-prefill`을 제공한다면 해당 문자열을 바꾼다.

## 실행 순서

1. 설정 셀에서 GPU 구성과 vLLM Python 경로를 지정한다.
2. 일반 vLLM 서버를 별도 터미널에서 시작한다.
3. UltraChat 질문에 target이 직접 응답하도록 하여 학습 데이터를 만들고, 별도 질문으로 일반 디코딩 시간을 측정한다.
4. 토큰·마스크 데이터를 전처리한다.
5. 일반 서버를 종료하고 hidden state 추출 서버를 시작한다.
6. hidden state를 저장한 뒤 추출 서버를 종료한다.
7. EAGLE-3를 학습한다.
8. 학습 체크포인트를 적용한 vLLM 서버를 시작하고 같은 질문으로 비교한다.
9. 서버를 종료한다.

GPU를 추출과 학습에 순서대로 사용하므로 B300 1개에서도 두 프로세스를 동시에 올리지 않는다. H100 프로필의 서버는 TP 4, 학습은 GPU 4개 분산 실행이다. B300 프로필은 모두 GPU 1개를 사용한다. `train_eagle3.py`는 GPU 학습을 별도 프로세스에서 실행한다.

기본값은 응답 512개, 최대 1,024토큰, 3 epoch이다. UltraChat의 기존 답변 대신 target이 생성한 토큰과 loss mask를 학습한다. thinking을 끈 greedy 응답이며 평가도 같은 조건을 사용한다. 생성 응답은 최대 256토큰으로 제한한다.

## 저장 항목

모든 실습 산출물은 실행 시 `output/`에 작성된다. 모델 다운로드는 Hugging Face의 기본 캐시를 사용한다.

| 위치 | 내용과 목적 |
| --- | --- |
| `target_responses.jsonl` | 생성 토큰과 loss mask: target 응답 학습 |
| `prepared/` | 전처리 토큰, 길이, 토큰 빈도·어휘 대응표 및 라이브러리 데이터 형식 정보 |
| `transfer/` | 서버에서 추출한 hidden state의 전달 작업 경로 |
| `hidden_states/` | 행별 hidden state: target을 올리지 않고 학습 |
| `checkpoints/` | 가중치, 모델 구조·target 참조·어휘 설정, optimizer·scheduler 상태, 검증 손실 |

노트북에는 Python 커널 정보만 넣는다. 별도 실행 식별자·체크섬·환경 보고서는 작성하지 않는다. Speculators v0.9.0의 학습 진입점은 `TrainConfig.save()`에서 Git SHA를 포함한 실행 이력을 기록하므로, `train_eagle3.py`는 이 호출만 비활성화한다. 이는 설치된 패키지 파일을 수정하지 않는 프로세스 내부 변경이다. 모델의 `save_pretrained()`와 학습 계산은 그대로 사용한다. 외부 실험 추적기는 켜지 않는다.

기존 데이터·캐시·체크포인트가 있는 폴더에 다른 실험을 섞지 않는다. 라이브러리가 캐시를 재사용하거나 학습을 재개할 수 있다. 설정이 다르면 노트북의 `OUTPUT`을 다른 빈 폴더로 지정한다.

## 자원과 결과 해석

Qwen3.8-27B의 언어 모델 BF16 가중치는 약 54GB이며 실행 메모리가 추가로 필요하다. hidden state는 기본 설정에서 텐서만 최대 약 20GiB이다. 모델 다운로드, draft·optimizer 체크포인트 공간은 별도다. GPU 학습 시간은 아직 측정하지 않았다.

평가는 `test_sft`의 16개 질문을 순차 요청한다. 전체 응답시간, 출력 토큰 처리량, greedy 토큰 일치 수, draft 채택률을 비교한다. 추출 서버의 성능은 측정하지 않는다. 학습 손실 감소와 추론 가속은 별개이며, 이 데이터 크기로 가속을 보장하지 않는다.

외부 유료 추론 API는 사용하지 않는다. 실행하면 회사 GPU 자원과 디스크를 사용하며, 모델과 공개 데이터가 없으면 다운로드한다. 저장된 결과만 읽을 때는 노트북 셀을 실행하지 않는다. 기존 `.env`는 사용하지 않는다.

## 확인 범위

노트북 구조·Python 문법과 GPU 호출을 대체한 H100·B300 실행 흐름을 검사했다. 토큰·마스크 대응, 추출·학습 층 설정, 성능 비교 계산과 실행 이력 저장의 비활성화를 확인했다. Qwen3.8-27B의 모델 구조, vLLM의 EAGLE-3 인터페이스와 Speculators CLI/API를 공식 소스와 대조했다. 실제 H100·B300에서의 학습 성공, 메모리 적합성, 채택률과 가속비는 미검증이다.

## 출처와 라이선스

- [vLLM speculative decoding](https://docs.vllm.ai/en/stable/features/speculative_decoding/)
- [Speculators 학습 가이드](https://docs.vllm.ai/projects/speculators/en/latest/user_guide/tutorials/train/)
- [Speculators 공식 오프라인 예제](https://github.com/vllm-project/speculators/blob/v0.9.0/examples/train/eagle3_llama3_8b_ultrachat_offline_5k.sh)
- [Hidden state extraction](https://docs.vllm.ai/en/stable/features/speculative_decoding/extract_hidden_states/)
- [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)
- [UltraChat 데이터](https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k)

vLLM·Speculators·Qwen3.8-27B는 Apache-2.0, UltraChat 데이터 카드는 MIT 라이선스를 명시한다. 공식 절차를 참고하여 이 실습의 설명과 코드를 작성했다.
