# Микросервисная архитектура исполнения моделей (FastAPI)

Три сервиса:

-**orchestrator** —принимает запрос, параллельно вызывает сервисы model_a и model_b,
объединяет их результаты и принимает финальное решение:
- approve — одобрить
- review — отправить на ручную проверку
- decline — отклонить

-**model_a** — сервис выявления аномалий транзакций (fraud detection).
Возвращает anomaly_score, список причин и вычисленные признаки.

-**model_b** — сервис оценки кредитного риска (risk scoring).
Возвращает pd_score, рекомендуемый лимит и причины.
## Запуск Вариант 1

Требования: Docker и Docker Compose.

```bash
docker compose up --build
```

После запуска:
- Оркестратор: http://localhost:8000
- Model A: http://localhost:8001
- Model B: http://localhost:8002

## Запуск Вариант 2

Требования: Python 3.10+ (рекомендуется 3.11).

```bash
# 1. Создать и активировать виртуальное окружение
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить все сервисы одной командой
python run_all.py
```
## Тестирование

| Файл                     | Описание                       |
| ------------------------ | ------------------------------ |
| `test_model_a.json`      | Запрос для Model A             |
| `test_model_b.json`      | Запрос для Model B             |
| `test_orchestrator.json` | Запрос для Orchestrator        |
| `test_review.json`       | Пример, где решение — `review` |
| `test_review_2.json`     | Ещё пример для `review`        |


## Запуск всех тестов

```bash
cd tests
powershell -ExecutionPolicy Bypass -File .\test_all.ps1

```
Пример запроса к Orchestrator:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d @tests/test_orchestrator.json

```
## Структура репозитория

```
banking-models/
│
├── model_a/                     # Сервис "Model A" — Fraud Detection
│   ├── app/
│   │   └── main.py              # Логика сервиса
│   ├── requirements.txt
│   └── Dockerfile
│
├── model_b/                     # Сервис "Model B" — Risk Scoring
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── orchestrator/                 # Оркестратор — объединяет результаты моделей
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── tests/                        # Тестовые запросы
│   ├── test_all.ps1              # Скрипт тестирования всех сервисов
│   ├── test_model_a.json
│   ├── test_model_b.json
│   ├── test_orchestrator.json
│   ├── test_review.json
│   └── test_review_2.json
│
├── docker-compose.yml            # Запуск всех сервисов через Docker
├── requirements.txt              # Зависимости для локального запуска
├── run_all.py                     # Запуск всех сервисов без Docker
├── run_all.sh                     # Linux/macOS запуск
├── run_all.bat                    # Windows запуск
└── README.md

```

## Заметки по архитектуре

- FastAPI для всех трёх сервисов.
- Оркестратор делает параллельные запросы к моделям через httpx.AsyncClient.
- Контракты сервисов:
- - POST /predict — входные данные в JSON, выход — JSON с результатами расчёта.
- Эндпоинт /healthz для проверки состояния сервиса.
- Лёгкая замена заглушек на реальные ML-модели.
- Возможность масштабирования через Docker Compose или Kubernetes.

## Дальнейшее развитие

- Подключение Kafka.
- Реальные ML-модели.
- Мониторинг, логирование и алертинг.
- Интеграция с CI/CD.

# Интеграции под стек 

## MLflow
- Модели (`model_a`, `model_b`) логируют метрики/параметры через `mlflow`.
- Трекер по умолчанию `file:./mlruns` (локальные файлы). Можно переопределить `MLFLOW_TRACKING_URI`.

## Airflow
- DAG: `airflow/dags/model_pipeline.py`
- Содержит задачу вызова оркестратора, печатает решение. Для локального демо можно запустить Airflow с docker-compose (не включён).

## Argo Workflows
- Шаблон: `argo/workflows/batch-score.yaml`
- Контейнер `curl` высылает батч-запрос к оркестратору. Переменная `ORCH_URL` может указывать на сервис в кластере.

## Kubernetes
- Манифесты: `k8s/manifests.yaml` (Namespace, ConfigMap, Deployments, Services).
- Образы  `image: python:3.11-slim` 
- Пороги для оркестратора вынесены в `ConfigMap`.

## Jenkins
- `Jenkinsfile`: стадии build → push → deploy. Требует настроенный Docker login и `kubectl` контекст.

## Запуск локально
- Как и раньше: `python run_all.py`
- Для логов MLflow: метрики будут сохраняться в `./mlruns`.
