# OpenDrift PlastDrift 기반 표층 미세플라스틱 확산 연구 웹 프로젝트

## 1. 프로젝트 개요

이 프로젝트는 OpenDrift의 `PlastDrift`를 이용해 `표층 해수에서 원유가 흡착된 미세플라스틱 입자군이 시간에 따라 어디까지 이동하고 얼마나 넓게 확산되는지`를 예측하고 분석하기 위한 연구용 로컬 웹 애플리케이션이다.

핵심 목적은 다음과 같다.

- 웹 화면에서 직접 시나리오를 입력하고 시뮬레이션을 실행한다.
- 시뮬레이션 결과를 지도, 그래프, 표, 이미지로 확인한다.
- 주요 산출물을 NetCDF, CSV, PNG, GIF, ZIP 형태로 관리하고 다운로드한다.
- 실험에서 얻은 경향을 시뮬레이션 매개변수와 비교 시나리오에 연결한다.

## 2. 연구 주제와의 연결

이 저장소는 다음 연구 주제를 지원하는 시나리오 실행 및 비교 도구이다.

`수환경과 미세플라스틱의 특성에 따른 원유 흡착량 비교 및 흡착 억제 용액 탐구`

현재 저장소에서 직접 다루는 비교 축은 다음과 같다.

- 미세플라스틱 종류 `PE`, `PP`, `PET`
- 해수 염분 `33 psu`, `40 psu`
- 기름 종류 `diesel`, `kerosene`
- 처리 전/처리 후 시나리오 비교
- 실험 조건 기록용 `temperature_c = 25.0` 메타데이터

실험에서 얻은 조건 차이는 시나리오 파라미터와 비교 리포트로 연결되며, 실행 결과는 이동거리, 중심 이동, 확산 면적, 관심 반경 도달 비율 등의 지표로 정리된다.

## 3. 연구 설계 반영 방식

이 프로젝트는 실험 조건을 아래 입자 매개변수에 연결하도록 구성되어 있다.

- `terminal_velocity`
- `wind_drift_factor`
- `current_drift_factor`

적용 방식은 다음과 같다.

- `configs/defaults.yaml`의 조합별 프리셋을 기본값으로 사용한다.
- 실험 결과에 맞춰 개별 시나리오의 이동 인자를 조정한다.
- 처리 전 시나리오와 처리 후 시나리오를 별도로 실행해 결과를 비교한다.

즉, 이 프로젝트는 `실험 조건 -> 시뮬레이션 파라미터 -> 표층 이동 범위 예측` 흐름으로 구성된 연구 워크플로를 제공한다.

## 4. 기본 설정

기본 설정은 `configs/defaults.yaml`과 예시 시나리오 파일에 반영되어 있다.

- 플라스틱 종류: `PE`, `PP`, `PET`
- 염분: `33 psu`, `40 psu`
- 기름 종류: `diesel`, `kerosene`
- 온도 메타데이터: `25.0`
- 표층 방출: `z = 0`
- 기본 모델 설정
    - `vertical_mixing = False`
    - `vertical_advection = False`
    - `stokes_drift = False`
- 기본 분석 시점: `24h`, `72h`, `168h`
- 기본 목표 반경: `50 km`

예시 시나리오(`configs/scenarios/*.json`)는 demo 입력을 사용하는 168시간 실행 예제로 구성되어 있다.

## 5. 주요 기능

### 웹 기능

- 시나리오 입력
- 저장된 시나리오 불러오기 / 저장하기
- 추천 프리셋 적용
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

## 6. 프로젝트 구조

```text
.
├── README.md
├── LICENSE
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

## 7. 설치 방법

### 7-1. pip 사용

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 7-2. conda 사용

```bash
conda env create -f environment.yml
conda activate plastdrift-surface-web
```

## 8. 입력 데이터 형식

### 실제 데이터 모드

실제 데이터 모드에서는 아래 두 파일을 준비한다.

- 해류 NetCDF 1개
- 바람 NetCDF 1개

검증기에서 확인하는 기본 조건은 다음과 같다.

#### 해류 파일

- `time` 좌표 포함
- `lat` 또는 `latitude` 좌표 포함
- `lon` 또는 `longitude` 좌표 포함
- 동서 방향 해류 성분
- 남북 방향 해류 성분

해류 성분은 `uo`, `vo`, `eastward_sea_water_velocity`, `northward_sea_water_velocity`, `x_sea_water_velocity`, `y_sea_water_velocity` 또는 해당 `standard_name`으로 식별한다.

#### 바람 파일

- `time` 좌표 포함
- `lat` 또는 `latitude` 좌표 포함
- `lon` 또는 `longitude` 좌표 포함
- `x_wind` 또는 `uwnd`
- `y_wind` 또는 `vwnd`

바람 성분은 `x_wind`, `y_wind`, `uwnd`, `vwnd` 또는 해당 `standard_name`으로 식별한다.

앱과 CLI는 실행 전에 기본적인 형식 검증을 수행한다.

### demo 모드

demo 모드에서는 합성 NetCDF를 자동 생성해 실행한다.

demo 모드는 다음 목적에 적합하다.

- 코드 동작 확인
- UI 점검
- 스모크 테스트
- 구조 시연

## 9. 웹 앱 실행 방법

```bash
streamlit run app.py
```

실행 후 브라우저에서 웹 인터페이스를 사용할 수 있다.

## 10. CLI 실행 방법

### 10-1. 단일 시나리오 실행

```bash
python main.py --config configs/scenarios/pe_33psu_diesel.json
```

### 10-2. 시나리오 검증만 수행

```bash
python main.py --config configs/scenarios/pe_33psu_diesel.json --validate-only
```

### 10-3. 배치 실행

```bash
python scripts/run_batch.py --dir configs/scenarios
```

### 10-4. 기존 결과의 GIF 재생성

```bash
python scripts/make_animation.py --result-dir data/output/pe_33psu_diesel_surface
```

### 10-5. 기존 결과의 보고서 재생성

```bash
python scripts/build_report.py --result-dir data/output/pe_33psu_diesel_surface
```

### 10-6. demo NetCDF 생성

```bash
python scripts/generate_demo_inputs.py --output-dir data/sample/generated
```

## 11. 출력 결과 구조

각 실행은 보통 `data/output/<output_name>/` 아래에 결과 폴더를 만들며, 같은 이름이 이미 있으면 `data/output/<output_name>_<timestamp>/` 형식으로 저장된다.

생성 가능한 주요 결과물은 다음과 같다.

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

demo 실행에서는 결과 폴더 아래 `demo_inputs/` 디렉터리에 합성 입력 NetCDF가 함께 저장된다.

시나리오 비교 결과는 다음 위치에 저장된다.

- `reports/figures/comparison_plot.png`
- `reports/summaries/scenario_comparison_summary.csv`
- `reports/summaries/scenario_comparison_report.md`
- `reports/summaries/batch_summary.csv`

## 12. 자동 분석 결과

시뮬레이션이 끝나면 5장에서 정리한 자동 분석 기능이 결과 파일과 그래프로 생성된다.

이 분석은 다음 비교 작업에 유용하다.

- `PE / PP / PET`, `33 / 40 psu`, `diesel / kerosene` 조합 간 비교
- 처리 전 시나리오와 처리 후 시나리오 간 비교
- 저장된 여러 결과 디렉터리의 교차 비교

## 13. 결과 해석 방법

### `summary.csv`

- 한 시나리오의 핵심 결과를 한 줄로 요약한 파일이다.
- 보고서 작성이나 시나리오 비교에 적합한 형식이다.

### `metrics.csv`

- 시간별 지표가 저장된 파일이다.
- 그래프 작성, 추가 분석, 비교 연구에 적합한 형식이다.

### `centroid_trajectory.csv`

- 시간에 따른 중심점 좌표와 중심 이동거리를 정리한 파일이다.
- 중심 이동 경로 비교에 적합한 형식이다.

### `trajectory_map.png`

- 방출점, 입자 궤적, centroid 이동, 최종 convex hull을 함께 보여주는 이미지이다.

### `snapshot_*h.png`

- 특정 시간대 주변의 입자 분포를 보여주는 이미지이다.

### `comparison_plot.png`

- 단일 실행 결과 폴더에서는 한 시나리오의 거리/면적 추이를 정리한 그래프이다.
- `reports/figures/comparison_plot.png`는 여러 시나리오를 함께 비교한 그래프이다.

### `analysis_report.md`

- 자동 생성되는 텍스트 요약 보고서이다.

## 14. 처리 전/후 시나리오 비교 방법

처리 전/후 비교는 별도의 시나리오를 만들어 실행하는 방식으로 진행한다.

1. 처리 전 조건을 `baseline scenario`로 정의한다.
2. 처리 후 조건을 `comparison scenario`로 정의한다.
3. 두 시나리오에서 `terminal_velocity`, `wind_drift_factor`, `current_drift_factor`를 설정한다.
4. 두 시나리오를 각각 실행한다.
5. 결과 폴더 또는 웹 UI의 비교 기능으로 이동거리, 확산 면적, 중심 이동량을 비교한다.

## 15. 테스트 방법

```bash
python -m pytest
```

현재 테스트는 다음을 포함한다.

- 설정 파일 로딩
- 분석 함수
- 입력 검증
- OpenDrift 기반 smoke run

## 16. 요약

본 프로젝트는 `실험 조건을 시뮬레이션 매개변수로 연결하여 원유가 흡착된 미세플라스틱의 표층 이동 범위를 예측하고 비교하는 연구용 웹/CLI 프로젝트`이다.
