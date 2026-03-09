# OpenDrift PlastDrift 기반 표층 미세플라스틱 확산 연구 웹 프로젝트

## 1. 프로젝트 개요

이 프로젝트는 OpenDrift의 `PlastDrift`를 이용하여, `표층 해수에서 원유가 흡착된 미세플라스틱 입자군이 시간에 따라 어디까지 이동하고 얼마나 넓게 확산되는지`를 예측하고 분석하기 위한 연구용 로컬 웹 애플리케이션입니다.

핵심 목적은 다음과 같습니다.

- 사용자가 웹 화면에서 직접 시나리오를 입력하고 시뮬레이션을 실행할 수 있도록 한다.
- 시뮬레이션 결과를 즉시 지도, 그래프, 표, 이미지로 확인할 수 있도록 한다.
- 결과 NetCDF, CSV, PNG, GIF, ZIP 파일을 웹에서 바로 다운로드할 수 있도록 한다.
- 실험에서 얻은 흡착 경향을 시뮬레이션 매개변수에 연결하는 `반경험적 연구 구조`를 제공한다.

이 프로젝트는 `자유 유막(free oil slick)의 weathering 모델`이 아니라, `원유가 흡착된 미세플라스틱 입자군의 표층 이동 범위 예측`을 목적으로 설계되어 있습니다.

## 2. 연구계획서와의 연결

이 저장소는 다음 연구 주제를 지원하기 위해 작성되었습니다.

`수환경과 미세플라스틱의 특성에 따른 원유 흡착량 비교 및 흡착 억제 용액 탐구`

연구계획서에서의 실험과 이 프로젝트의 시뮬레이션은 다음처럼 연결됩니다.

### 실험 파트

- 미세플라스틱 종류 `PE`, `PP`, `PET` 비교
- 해수 염분 `33 psu`, `40 psu` 비교
- 기름 종류 `diesel`, `kerosene` 비교
- 실험 온도 `25℃` 고정
- UV-Vis를 이용한 흡착량 비교
    - 특히 `250~270 nm` 부근 피크 중심 분석
- 흡착량이 가장 큰 조건 확인
- `Tween 20`, `구연산`, `베이킹 소다`를 이용한 탈착 또는 흡착 억제 효과 비교

### 시뮬레이션 파트

- 실험에서 흡착량이 크거나 작게 나타난 조건을 시나리오로 구성
- 표층 해수에서 해당 입자군이 해류와 바람에 따라 어떻게 이동하는지 예측
- 이동 거리, 중심 이동, 확산 면적, 외곽 범위, 관심 반경 도달 비율 등을 정량화
- 처리 전/처리 후 시나리오를 비교하여 확산 저감 가능성을 평가

즉, 이 프로젝트는 실험을 대체하는 것이 아니라, `실험에서 얻은 흡착/억제 경향을 실제 해양 이동 시나리오로 연결`하기 위한 수치 해석 도구입니다.

## 3. 연구 설계 반영 방식

이 프로젝트는 흡착 화학 반응 자체를 직접 계산하지 않습니다. 대신 실험 결과를 아래와 같은 입자 매개변수에 반영할 수 있게 설계되어 있습니다.

- `terminal_velocity`
- `wind_drift_factor`
- `current_drift_factor`

예를 들어:

- 어떤 조건에서 미세플라스틱이 기름을 많이 흡착했다면
    - 표면 거동이 달라졌다고 가정하여 `wind_drift_factor`를 조정할 수 있습니다.
- 밀도 변화나 부유 특성이 달라졌다고 판단되면
    - `terminal_velocity`를 조정할 수 있습니다.
- 처리 용액 적용 후 확산 경향이 줄어드는 것으로 해석되면
    - 별도의 `post-treatment` 시나리오를 만들어 처리 전과 비교할 수 있습니다.

따라서 본 프로젝트는 `실험 결과 -> 시뮬레이션 파라미터 -> 표층 이동 범위 예측`의 구조를 갖는 반경험적 연구 프레임워크입니다.

## 4. 기본 연구 조건

프로젝트 기본 설정은 연구계획서의 조건을 반영합니다.

- 플라스틱 종류: `PE`, `PP`, `PET`
- 염분: `33 psu`, `40 psu`
- 기름 종류: `diesel`, `kerosene`
- 온도: `25℃` 고정 메타데이터
- 표층 방출: `z = 0`
- 기본 표층 모델 설정
    - `vertical_mixing = False`
    - `vertical_advection = False`
    - `stokes_drift = False`

필요할 경우 `stokes_drift`는 시나리오 옵션에서 켤 수 있습니다.

## 5. 이 프로젝트가 하는 일 / 하지 않는 일

### 하는 일

- 원유가 흡착된 것으로 가정한 미세플라스틱 입자군의 표층 이동 시뮬레이션
- 해류 NetCDF, 바람 NetCDF를 이용한 실제 강제력 기반 실행
- 결과 지도, 궤적, 스냅샷, GIF, 정량 분석 자동 생성
- 여러 조건 간 비교 분석

### 하지 않는 일

- 직접적인 흡착 화학 계산
- `Tween 20`, `구연산`, `베이킹 소다`의 분자 수준 탈착 반응 계산
- 원유 weathering 모델링
- 실험값 없이 자동으로 “정답” 매개변수를 산출하는 기능

즉, 이 프로젝트는 `화학 반응 시뮬레이터`가 아니라 `실험 결과를 반영할 수 있는 표층 확산 예측기`입니다.

## 6. 주요 기능

### 웹 기능

- 시나리오 입력
- 저장된 시나리오 불러오기 / 저장하기
- current/wind NetCDF 경로 입력 또는 파일 업로드
- 시뮬레이션 실행
- 단계별 진행 상태 표시
- 지도, 그래프, 표, 이미지 확인
- 결과 파일 다운로드
- 시나리오 비교
- 로그 및 manifest 확인

### CLI 기능

- 단일 시나리오 실행
- 시나리오 유효성 검사
- 배치 실행
- GIF 재생성
- Markdown 보고서 재생성
- demo 입력 NetCDF 생성

### 자동 분석 기능

- 24h / 72h / 168h 최대 이동거리
- 평균 이동거리
- centroid 이동량
- centroid trajectory
- convex hull 면적
- 확산 반경 변화
- 관심 반경 도달 비율
- 관심 영역(bbox) 도달 비율
- 표층 체류 비율
- 시나리오 비교 요약

## 7. 프로젝트 구조

```text
.
├── README.md
├── requirements.txt
├── environment.yml
├── app.py
├── main.py
├── configs
│   ├── defaults.yaml
│   └── scenarios
│       ├── pe_33psu_diesel.json
│       ├── pp_33psu_diesel.json
│       └── pet_40psu_kerosene.json
├── data
│   ├── input
│   │   └── uploads
│   ├── output
│   └── sample
│       └── README.md
├── reports
│   ├── figures
│   └── summaries
├── scripts
│   ├── build_report.py
│   ├── generate_demo_inputs.py
│   ├── make_animation.py
│   ├── run_batch.py
│   └── run_scenario.py
├── src
│   ├── analysis
│   ├── simulation
│   ├── ui
│   └── utils
└── tests
    ├── test_config_loader.py
    ├── test_metrics.py
    ├── test_runner_smoke.py
    └── test_validation.py
```

## 8. 설치 방법

### 8-1. pip 사용

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 8-2. conda 사용

```bash
conda env create -f environment.yml
conda activate plastdrift-surface-web
```

## 9. 입력 데이터 형식

### 실제 데이터 모드

사용자는 아래 두 파일을 준비해야 합니다.

- 해류 NetCDF 1개
- 바람 NetCDF 1개

권장 형식:

#### 해류 파일

- 동서 방향 해류 성분
- 남북 방향 해류 성분
- `time`, `lat`, `lon` 좌표 포함

#### 바람 파일

- `x_wind`
- `y_wind`
- `time`, `lat`, `lon` 좌표 포함

앱은 실행 전에 기본적인 형식 검증을 수행합니다.

### demo 모드

외부 해양 데이터를 포함하지 않기 때문에, demo 모드에서는 합성 NetCDF를 자동 생성합니다.

demo 모드는 다음 목적에만 사용해야 합니다.

- 코드 동작 확인
- UI 점검
- 스모크 테스트
- 외부 데이터 없이 구조 시연

demo 모드는 실제 해양 예측 결과가 아닙니다.

## 10. 웹 앱 실행 방법

```bash
streamlit run app.py
```

실행 후 브라우저에서 다음 작업을 할 수 있습니다.

- 시나리오 입력
- 저장된 시나리오 로드
- 시뮬레이션 실행
- 실행 상태 확인
- 결과 지도 및 그래프 확인
- CSV / PNG / GIF / NetCDF / ZIP 다운로드

## 11. CLI 실행 방법

### 11-1. 단일 시나리오 실행

```bash
python main.py --config configs/scenarios/pe_33psu_diesel.json
```

### 11-2. 시나리오 검증만 수행

```bash
python main.py --config configs/scenarios/pe_33psu_diesel.json --validate-only
```

### 11-3. 배치 실행

```bash
python scripts/run_batch.py --dir configs/scenarios
```

### 11-4. 기존 결과의 GIF 재생성

```bash
python scripts/make_animation.py --result-dir data/output/pe_33psu_diesel_surface
```

### 11-5. 기존 결과의 보고서 재생성

```bash
python scripts/build_report.py --result-dir data/output/pe_33psu_diesel_surface
```

### 11-6. demo NetCDF 생성

```bash
python scripts/generate_demo_inputs.py --output-dir data/sample/generated
```

## 12. 출력 결과 구조

각 실행은 보통 `data/output/<scenario_name>/` 아래에 결과 폴더를 만듭니다.

생성 가능한 주요 결과물:

- `result.nc`
- `summary.csv`
- `metrics.csv`
- `centroid_trajectory.csv`
- `scenario_config_copy.json`
- `resolved_scenario.json`
- `manifest.json`
- `trajectory_map.png`
- `convex_hull_map.png`
- `snapshot_24h.png`
- `snapshot_72h.png`
- `snapshot_168h.png`
- `animation.gif`
- `comparison_plot.png`
- `centroid_distance_plot.png`
- `dispersion_area_plot.png`
- `analysis_report.md`
- `run.log`
- `results_bundle.zip`

시나리오 비교 결과는 다음 위치에 저장됩니다.

- `reports/figures/comparison_plot.png`
- `reports/summaries/scenario_comparison_summary.csv`
- `reports/summaries/scenario_comparison_report.md`

## 13. 자동 분석 결과

시뮬레이션이 끝나면 다음 분석이 자동 수행됩니다.

- 24시간, 72시간, 168시간 후 최대 이동거리
- 초기 방출점으로부터의 평균 이동거리
- 입자군 중심(centroid) 이동량
- 시간에 따른 centroid trajectory
- 조건별 확산 면적
- convex hull 기반 외곽 범위 면적
- 시간에 따른 확산 반경 변화
- 특정 반경 도달 입자 비율
- 특정 관심 영역 도달 비율
- 표층 체류 비율
- 시나리오 간 비교 요약

이 분석은 연구계획서의 목적에 맞게 다음 두 종류의 비교에 특히 유용합니다.

- `PE / PP / PET`, `33 / 40 psu`, `diesel / kerosene` 조합 간 비교
- 처리 전 시나리오와 처리 후 시나리오 간 비교

## 14. 결과 해석 방법

### `summary.csv`

- 한 시나리오의 핵심 결과를 한 줄로 요약한 파일입니다.
- 보고서 작성이나 시나리오 비교에 적합합니다.

### `metrics.csv`

- 시간별 지표가 저장된 파일입니다.
- 그래프 작성, 추가 분석, 비교 연구에 적합합니다.

### `trajectory_map.png`

- 방출점, 입자 궤적, centroid 이동, 최종 convex hull을 함께 보여줍니다.

### `snapshot_*h.png`

- 특정 시간대 주변의 입자 분포를 보여줍니다.

### `comparison_plot.png`

- 시나리오별 최대 이동거리와 확산 면적을 비교합니다.

### `analysis_report.md`

- 자동 생성되는 텍스트 요약 보고서입니다.

## 15. 처리 용액 연구와의 연결 방법

연구계획서에서는 `Tween 20`, `구연산`, `베이킹 소다`를 이용한 흡착 억제 또는 탈착 효과를 실험적으로 비교하도록 설계되어 있습니다.

이 프로젝트에서는 이들을 직접 화학 반응으로 계산하지 않고 다음처럼 연결하는 것을 권장합니다.

1. 실험에서 처리 전후 흡착량 차이를 측정한다.
2. 처리 전 조건을 `baseline scenario`로 정의한다.
3. 처리 후 조건을 `post-treatment scenario`로 정의한다.
4. 처리 후 시나리오에서 `terminal_velocity`, `wind_drift_factor`, `current_drift_factor`를 보정한다.
5. 두 시나리오의 이동거리, 확산면적, centroid 이동량을 비교한다.

이 방식은 연구계획서의 화학 실험 결과를 해양 확산 시뮬레이션으로 연결하는 실용적인 방법입니다.

## 16. 테스트 방법

```bash
python -m pytest
```

현재 테스트는 다음을 포함합니다.

- 설정 파일 로딩
- 분석 함수
- 입력 검증
- OpenDrift 기반 짧은 smoke run

스모크 테스트는 합성 forcing을 이용해 실제 `PlastDrift` 실행 경로를 끝까지 확인합니다.

## 17. 현재 확인된 실행 상태

직접 확인한 항목:

- `python -m pytest -q` 통과
- 예시 시나리오 CLI 실행 성공
- Streamlit 앱 기본 기동 확인

직접 확인하지 못한 항목:

- 사용자가 제공하는 실제 해류/바람 NetCDF에 대한 모든 경우의 수
- 장시간 대규모 시뮬레이션의 성능 한계
- 모든 브라우저 환경에서의 UI 동작

## 18. 알려진 한계

- 기본 구현은 표층 전용이며 oil weathering을 모델링하지 않습니다.
- 흡착 및 탈착 화학 반응은 직접 계산하지 않습니다.
- 실험 데이터 없이 자동 보정된 “정답 파라미터”를 제공하지 않습니다.
- demo 모드는 합성 데이터이므로 실제 해양 예측으로 해석하면 안 됩니다.
- 사용자가 제공하는 NetCDF의 공간 범위와 시간 범위가 충분하지 않으면 실행이 실패하거나 의미 있는 결과가 나오지 않을 수 있습니다.
- 현재 애니메이션 출력은 `GIF`이며 `MP4`는 기본 제공하지 않습니다.
- 입력 화면의 지도 클릭 좌표 선택은 아직 구현하지 않았습니다.

## 19. 향후 확장 아이디어

- 지도 클릭 기반 방출 위치 선택
- 다각형 관심 해역 입력
- 처리 전/후 시나리오 자동 비교 템플릿
- 실험 데이터 기반 파라미터 보정 워크플로
- FFmpeg 사용 가능 시 MP4 출력 지원
- GeoJSON 등 GIS 친화적 출력 추가
- 장시간 실행을 위한 백그라운드 작업 구조

## 20. 요약

이 프로젝트는 다음 질문에 답하기 위한 도구입니다.

- 어떤 미세플라스틱이 어떤 조건에서 기름을 더 많이 흡착하는가?
- 그런 조건에서 표층 해수에서 얼마나 멀리, 얼마나 넓게 퍼질 수 있는가?
- 흡착 억제 또는 탈착 용액이 실제 확산 범위를 줄이는 데 도움이 될 수 있는가?

즉, 본 프로젝트는 `실험 결과를 시뮬레이션 매개변수로 연결하여, 원유가 흡착된 미세플라스틱의 표층 이동 범위를 예측하는 연구용 웹 프로젝트`입니다.
