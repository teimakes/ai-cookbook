# 추론 소프트웨어와 성능 측정

[4장 발표 자료](https://teimakes.github.io/ai-cookbook/)를 브라우저에서 바로 열 수 있습니다. [실습 노트북 목록](https://teimakes.github.io/ai-cookbook/#lab)에서 장비에 맞는 노트북을 선택하세요. [커널과 커널 융합](https://teimakes.github.io/ai-cookbook/kernel-fusion.html)은 사진 예제만 따로 볼 때 사용합니다.

[H100 네 장에서 Gemma 4와 DFlash 비교하기](vllm-gemma4-dflash.ipynb)에서는 같은 질문으로 Gemma 단독 실행과 DFlash의 답변, 처리량, 전체 응답 시간을 비교합니다. 개념 설명은 20분입니다. 발표 전에 노트북 1~6절을 측정하고 7절까지 출력을 저장한 뒤, 현장에서는 7절만 10분간 시연합니다.

아래 두 노트북은 Qwen3.8-27B를 사용합니다. 입력과 출력 길이, 동시 요청 수를 바꾸며 성능을 측정합니다.

| 환경 | 노트북 | 직접 실행 | 서버 실행 |
| --- | --- | --- | --- |
| 한 서버의 H100 GPU 4개 | [h100.ipynb](h100.ipynb) | GPU 1개 | GPU 4개, TP 4 |
| B300 GPU 1개 | [b300.ipynb](b300.ipynb) | GPU 1개 | GPU 1개, TP 1 |

H100 4개가 여러 서버에 나뉜 구성은 포함하지 않는다. H100 4개와 B300 1개를 비교한 서버 결과에는 GPU 수와 GPU 간 통신 차이도 포함된다.

## Qwen 실습 준비

- Linux에서 각 GPU를 지원하는 vLLM·PyTorch·CUDA 환경과 Jupyter 커널을 사용한다.
- 노트북은 기존 vLLM 가상환경의 Python 커널로 실행한다. 패키지를 자동 설치하거나 교체하지 않는다.
- Qwen3.8-27B를 지원하는 환경이 필요하다. [공식 vLLM 실행 안내](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)는 vLLM 0.17.0 이상과 Transformers 5.8.0 이상을 안내한다. 아래 벤치마크 옵션의 지원 여부는 별도로 확인한다.
- `requirements.txt`에 추가 의존성은 없다. 회사 환경의 패키지 버전은 아직 확인하지 않았으며 GPU 실행을 검증한 버전도 없다.
- vLLM의 `serve`, `bench serve` 명령과 `--num-warmups`, `--max-concurrency`, `--percentile-metrics`, `--metric-percentiles` 옵션이 필요하다. 설치 환경의 `vllm bench serve --help`로 확인한다.
- 서버의 접두사 캐시 해제 옵션은 현재 공식 문서의 `--disable-prefix-caching`을 사용한다. 설치 버전이 `--no-enable-prefix-caching`을 제공하면 노트북의 해당 문자열을 바꾼다.
- GPU 할당, 가상환경, Jupyter 셀 실행, 토큰화와 자기회귀 생성에 대한 기초 지식을 전제로 한다.

## 실행

1. 이 폴더 전체를 각 GPU 머신에서 사용할 수 있게 준비한다.
2. 이 폴더를 작업 디렉터리로 열고 해당 노트북의 설정 셀부터 실행한다.
3. 기본 모델 `Qwen/Qwen3.8-27B`를 사용하거나, `MODEL`을 양쪽 환경에 준비한 동일한 모델의 로컬 경로로 바꾼다. 기본값은 BF16이며 양자화하지 않는다.
4. 직접 실행 비교 셀을 실행한다. `transformers_baseline.py`와 `vllm_baseline.py`는 각각 별도 프로세스에서 모델을 실행한다.
5. 노트북이 출력한 서버 실행 명령을 같은 머신의 별도 터미널에서 실행한다. 서버가 시작된 뒤 응답 확인 셀로 이동한다.
6. 동시 요청 수, 입력 길이, 출력 길이를 바꾸는 측정 셀을 차례로 실행한다.
7. 서버 터미널에서 `Ctrl+C`로 종료한다.

27B 언어 모델 가중치는 BF16 기준 약 54GB이며, 캐시·중간 텐서·커널 작업 공간에는 추가 메모리가 필요하다. 직접 실행 비교는 GPU 1개를 사용하므로 해당 GPU의 가용 메모리가 충분해야 한다. Transformers는 시각 인코더도 로드하지만 텍스트만 입력하고, vLLM은 `language_model_only`로 시각 인코더를 제외한다. 두 경로의 GPU 메모리 사용량을 비교하는 실험은 아니다.

Transformers의 로더는 `Qwen3_5ForConditionalGeneration`을 사용한다. 클래스 이름에 3.5가 포함되어 있지만, Qwen3.8-27B의 [공식 모델 설정](https://huggingface.co/Qwen/Qwen3.8-27B/blob/main/config.json)에 지정된 구조다.

기본 직접 실행 비교는 입력 512토큰 × 요청 8개, 출력 128토큰을 사용한다. vLLM의 동시 처리 상한도 8개로 지정한다. 워밍업 2회 후 3회 측정하며, 각 측정의 실제 출력 합계는 1,024토큰이다.

서버 응답 확인에서는 `enable_thinking=False`로 직접 답변을 받는다. 성능 측정은 채팅 템플릿을 사용하지 않는 합성 입력과 고정 출력 길이를 사용하므로 thinking 모드 간 비교가 아니다.

서버 실험은 조건마다 요청 256개, 워밍업 요청 8개, 본 측정 3회를 사용한다. 동시 요청 수 4조건, 입력 길이 3조건, 출력 길이 3조건으로 총 30회 벤치마크를 실행한다. 총 본 측정 요청 수는 7,680개이며 도구의 워밍업과 사전 동작 확인 요청은 별도다.

노트북에서 `NUM_PROMPTS`와 `REPEATS`를 줄이면 실행 점검에 사용할 수 있다. 적은 요청 수의 p95를 충분한 부하에서 측정한 값으로 해석하지 않는다.

## 출력과 해석

- 직접 실행: 경과 시간, 실제 출력 토큰 수, 출력 토큰 처리량.
- 서버 측정: 성공·실패 요청 수, 입력·출력 토큰 수, 처리량, TTFT·TPOT·전체 응답시간의 p50·p95.
- 출력은 노트북 셀에 표시하며 별도 결과 파일을 작성하지 않는다. 저장된 노트북 결과만 읽을 때는 셀을 실행하지 않는다.
- 합성 입력과 고정 출력 길이로 성능을 측정한다. 답변 품질이나 실제 서비스 트래픽을 평가하지 않는다.
- 서버 측정은 요청 발생률 제한 없이 동시 요청 상한을 유지하는 방식이다. 고정된 초당 요청 수 실험과 구분한다.
- TP 4가 TP 1보다 빠르다고 가정하지 않는다. 두 환경의 GPU 수·통신·패키지·CPU·드라이버 차이까지 포함한 결과다.
- Qwen3.8-27B는 선형 어텐션과 전체 어텐션을 함께 사용한다. 측정 차이를 PagedAttention 하나의 효과로 설명하지 않는다.
- 외부 유료 추론 API를 호출하지 않는다. 실행 중 회사 GPU 자원을 사용하며 모델이 없으면 Hugging Face 다운로드가 발생한다.

## 확인 범위

노트북 구조와 Python 문법을 확인했다. GPU 실행과 HTTP 호출을 대체한 검사에서 두 노트북의 직접 실행 명령 2개, 서버 설정, 벤치마크 30개의 입력·출력 길이와 동시 요청 조건을 확인했다.

노트북과 코드는 GPU 실측 결과를 포함하지 않는다. H100·B300 실행, 회사 환경의 vLLM 버전 호환성, 실제 성능 수치는 미확인이다. CLI 옵션과 합성 데이터 길이 설정은 현재 공식 문서 기준이며, 이전 버전에서는 옵션 이름뿐 아니라 의미도 다를 수 있다.

노트북과 Python 파일의 문법은 저장소 루트에서 다음 명령으로 검사한다. API를 호출하지 않는다.

```bash
python scripts/check_notebooks.py
```

## 출처

- [Inference Korea 일정](https://songys.github.io/inference-korea/)
- [Inference Engineering 4장](https://corazzon.github.io/inference-engineering/ko/04-소프트웨어.html)
- [vLLM CLI: serve](https://docs.vllm.ai/en/stable/cli/serve/)
- [vLLM CLI: bench serve](https://docs.vllm.ai/en/stable/cli/bench/serve/)
- [vLLM 병렬화](https://docs.vllm.ai/en/stable/serving/parallelism_scaling/)
- [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B): Apache-2.0 모델.
- [PagedAttention 논문](https://arxiv.org/abs/2309.06180)

발표에 사용한 사진과 그림의 출처는 각 그림 아래에 표시했습니다.
