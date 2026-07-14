# 🛡️ NetworkSecurity — Phishing Website Detection (End-to-End MLOps Pipeline)

An end-to-end, production-style MLOps pipeline that ingests raw website/URL feature data, validates and transforms it, trains and evaluates a classifier, tracks every experiment, and ships the winning model as a containerized, CI/CD-deployed prediction API.

**Repository:** [github.com/Michael-Segun/Networksecurity](https://github.com/Michael-Segun/Networksecurity)

---

## 1. Problem Statement

Phishing websites imitate legitimate ones to steal credentials, financial information, and personal data. Manually blacklisting URLs doesn't scale — new phishing domains appear constantly, and static blocklists always lag behind attackers.

This project solves that problem by framing phishing detection as a **supervised binary classification task**. Given a set of structural, lexical, and behavioral features extracted from a website/URL (e.g., URL length, use of IP address, presence of `@` symbol, SSL certificate status, domain age, abnormal redirects, iframe usage, etc.), the model predicts whether the site is:

- **Legitimate** (safe), or
- **Phishing** (malicious)

The goal is not just a notebook with a good F1 score — it's a repeatable, monitorable, and deployable pipeline that mirrors how this kind of model would actually be operated in a real security product: data lands in a database → gets validated against a schema → gets transformed → a model gets trained, evaluated, and versioned → the best model is packaged and shipped to production behind an API.

### Industries this project is relevant to

- **Cybersecurity vendors & SOC/SIEM platforms** — real-time URL/domain reputation scoring as a threat-intel feature
- **Banking, Fintech & Payments** — protecting customers from phishing pages that spoof login/checkout flows
- **Email Security & Gateways** — scanning links in inbound email before they reach a user's inbox
- **Telecom & ISPs** — network-level filtering of malicious domains at the DNS/gateway layer
- **E-commerce & Retail** — brand protection against fake storefronts and checkout clones
- **Browser vendors & Endpoint Security** — powering "Safe Browsing"-style warnings
- **Government & Critical Infrastructure** — securing citizen-facing portals and internal networks

---

## 2. Tech Stack & Tools

| Layer | Tools / Libraries |
|---|---|
| Language | Python |
| Data storage | MongoDB (`pymongo`, `pymongo[srv]`) |
| Data science | pandas, numpy, scikit-learn |
| Missing value handling | `KNNImputer` (scikit-learn) |
| Experiment tracking | MLflow, hosted/remote-tracked via DagsHub |
| Serialization | `dill` (models/preprocessors), `pyaml`/YAML (schema & reports) |
| API serving | FastAPI + Uvicorn, python-multipart |
| Config/secrets | python-dotenv |
| Containerization | Docker |
| Cloud | AWS — S3 (training bucket), ECR (image registry), EC2 (self-hosted runner / serving host) |
| CI/CD | GitHub Actions (3-stage: Integration → Build & Push to ECR → Continuous Deployment on self-hosted EC2 runner) |
| Templating (API UI) | Jinja2 `templates/` (HTML, served via FastAPI) |

---

## 3. Project Architecture — Pipeline Stages

The pipeline follows a modular, config-driven ML pipeline architecture (`networksecurity/` package), where every run produces a timestamped, versioned `Artifacts/` directory. This mirrors industry-standard staged pipelines used in production ML systems (à la Kubeflow/TFX-style pipelines, just self-orchestrated in Python).

```
Raw Data (MongoDB)
        │
        ▼
[1] Data Ingestion
        │  → train.csv / test.csv
        ▼
[2] Data Validation
        │  → schema check + drift report
        ▼
[3] Data Transformation
        │  → KNN-imputed, transformed feature arrays + preprocessing.pkl
        ▼
[4] Model Trainer
        │  → trained model + train/test metrics
        ▼
[5] Model Evaluation & Registry (MLflow via DagsHub)
        │
        ▼
[6] Packaging (final_model/) → Docker Image → ECR → EC2 → FastAPI serving
```

Each stage below follows the same three-part contract used throughout the pipeline: **Config** (what drives its behavior), **Component** (what the stage actually does), and **Artifact** (what it hands off to the next stage).

### Stage 1 — Data Ingestion

**Config**

| Constant | Value |
|---|---|
| `DATA_INGESTION_COLLECTION_NAME` | `NetworkData` |
| `DATA_INGESTION_DATABASE_NAME` | `SegunMichael` |
| `DATA_INGESTION_DIR_NAME` | `data ingestion` |
| `DATA_INGESTION_FEATURE_STORE_DIR` | `feature_store` |
| `DATA_INGESTION_INGESTED_DIR` | `ingested` |
| `DATA_INGESTED_TRAIN_TEST_SPLIT_RATION` | `0.2` |

**Component**

- `Data_Ingestion` class connects to MongoDB and pulls the `NetworkData` collection from the `SegunMichael` database into a Pandas DataFrame.
- The raw pull is exported to a feature store directory (an untouched snapshot of what came out of Mongo, kept separate from the split files so the original pull stays traceable).
- A train/test split (`split_data_as_train_test`) is then performed using the 0.2 ratio, and both splits are exported to the `ingested/` folder.

**Artifact**

```python
DataIngestionArtifact(
    trained_file_path='Artifacts/.../data ingestion/ingested/train.csv',
    test_file_path='Artifacts/.../data ingestion/ingested/test.csv'
)
```

This artifact is what gets passed into Data Validation — the next stage never touches MongoDB or the feature store directly, only these two file paths.

### Stage 2 — Data Validation

**Config**

| Constant | Value |
|---|---|
| `DATA_VALIDATION_DIR_NAME` | `data_validation` |
| `DATA_VALIDATION_VALID_DIR` | `validation` |
| `DATA_VALIDATION_INVALID_DIR` | `invalid` |
| `DATA_VALIDATION_DRIFT_REPORT_DIR` | `drift_report` |
| `DATA_VALIDATION_DRIFT_REPORT_FILE_NAME` | `report.yaml` |
| `SCHEMA_FILE_PATH` | `data_schema/schema.yaml` |

**Component**

Purpose: guard the pipeline from silently training on malformed, incomplete, or drifted data — a standard MLOps safeguard sitting between ingestion and transformation.

- **Schema check:** the ingested train/test DataFrames are validated against `data_schema/schema.yaml`, confirming the expected column count (31 columns) is present before proceeding. A mismatch routes the data to `invalid/` instead of letting it continue downstream.
- **Data drift detection:** this is the stage where the drift report is generated. Train and test distributions are statistically compared column-by-column, and the results — including whether drift was detected per feature — are written to a structured `report.yaml` under `drift_report/`. This gives an auditable, versioned record of whether the held-out test set still reflects the training distribution, which is essential for catching data quality issues before they silently degrade model performance downstream.
- Data passing both checks is written to `validation/`; anything failing is isolated in `invalid/`.

**Artifact**

```python
DataValidationArtifact(
    validation_status=True/False,
    valid_train_file_path='Artifacts/.../data_validation/validation/train.csv',
    valid_test_file_path='Artifacts/.../data_validation/validation/test.csv',
    invalid_train_file_path=...,
    invalid_test_file_path=...,
    drift_report_file_path='Artifacts/.../data_validation/drift_report/report.yaml'
)
```

### Stage 3 — Data Transformation

**Config**

| Constant | Value |
|---|---|
| `DATA_TRANSFORMATION_DIR_NAME` | `data_transformation` |
| `DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR` | `transformed` |
| `DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR` | `transformed_object` |
| `DATA_TRANSFORMATION_IMPUTER_PARAMS` | `{missing_values: nan, n_neighbors: 3, weights: 'uniform'}` |
| `PREPROCESSING_OBJECT_FILE_NAME` | `preprocessing.pkl` |
| `TARGET_COLUMN` | `Result` |

**Component**

`DataTransformation` class, entry point `initiate_data_transformation()`.

- `get_data_transformer_object()` builds a preprocessing pipeline centered on a `KNNImputer` (`n_neighbors=3`, `weights='uniform'`) to fill missing feature values.
- The imputer is fit on the **training split only**, then used to `transform()` both train and test splits — standard practice to prevent test-set leakage into the imputation logic.
- The target column (`Result`) is separated from the feature matrix before transformation and re-attached afterward.
- The transformed feature matrices are converted to NumPy arrays and saved as `.npy` files (not CSV). This is a deliberate choice at this stage — `.npy` preserves exact dtypes and loads considerably faster than CSV for the model training step that follows immediately after, since no re-parsing or type inference is needed.
- The fitted imputer/preprocessor object is serialized separately via `MainUtils.save_object()` as `preprocessing.pkl`, so the exact same transformation can be re-applied at inference time in production (this is the object later shipped inside `final_model/`).

**Artifact**

```python
DataTransformationArtifact(
    transformed_object_file_path='Artifacts/.../data_transformation/transformed_object/preprocessing.pkl',
    transformed_train_file_path='Artifacts/.../data_transformation/transformed/train.npy',
    transformed_test_file_path='Artifacts/.../data_transformation/transformed/test.npy'
)
```

### Stage 4 — Model Trainer

**Config**

| Constant | Value |
|---|---|
| `MODEL_TRAINER_DIR_NAME` | `model_trainer` |
| `MODEL_TRAINER_TRAINED_MODEL_DIR` | `trained_model` |
| `MODEL_TRAINER_TRAINED_MODEL_NAME` | `model.pkl` |
| `MODEL_TRAINER_EXPECTED_SCORE` | `0.6` |
| `MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD` | `0.05` |

**Component**

- Loads the transformed `.npy` train/test arrays produced in Stage 3 (fast load, no re-parsing needed).
- Trains and compares multiple candidate classifiers — **Random Forest, Decision Tree, Gradient Boosting, Logistic Regression, AdaBoost** — via `GridSearchCV`, scoring each on F1, Precision, and Recall across both train and test splits.
- Applies two gates before accepting a model:
  - **Minimum performance gate** — test score must exceed `MODEL_TRAINER_EXPECTED_SCORE` (0.6).
  - **Overfitting/underfitting gate** — the gap between train and test scores must stay within `MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD` (0.05), rejecting models that memorize the training set.
- The winning model (**Random Forest**) and its fitted preprocessor are serialized together via `MainUtils.save_object()`.
- **Experiment tracking:** every run's parameters, metrics, and model artifact are logged to MLflow, tracked remotely through DagsHub (`Michael-Segun/Networksecurity` repo), giving a permanent, comparable history of every training run.

**Artifact**

```python
ModelTrainerArtifact(
    trained_model_file_path='Artifacts/.../model_trainer/trained_model/model.pkl',
    train_metric_artifact=ClassificationMetricArtifact(f1_score=..., precision_score=..., recall_score=...),
    test_metric_artifact=ClassificationMetricArtifact(f1_score=..., precision_score=..., recall_score=...)
)
```

### Stage 5 — Model Evaluation & Registry

All runs are visible and comparable on the DagsHub MLflow UI, enabling side-by-side comparison of algorithms and hyperparameters before promoting a model to `final_model/`.

The **Random Forest** run was the one promoted — it cleared both the performance and overfitting gates from Stage 4 with the best test-set F1/Precision/Recall of all logged runs.

### Stage 6 — Packaging, CI/CD & Serving

- `final_model/` holds the production-selected model + preprocessor.
- `app.py` — FastAPI application serving predictions (with Jinja2 `templates/` for a simple web UI) and writing results to `prediction_output/`.
- `Dockerfile` — containerizes the app for deployment.
- **CI/CD** (`.github/workflows`) — 3-job GitHub Actions pipeline:
  1. **Continuous Integration** — checkout, lint, unit tests.
  2. **Continuous Delivery** — builds the Docker image and pushes it to AWS ECR.
  3. **Continuous Deployment** — a self-hosted runner on EC2 pulls the latest ECR image and runs it (`docker run -d -p 8080:8080 ...`), with AWS credentials injected as environment variables and old images pruned automatically.

---

## 4. Configuration Reference (`training_pipeline` constants)

| Constant | Value | Purpose |
|---|---|---|
| `TARGET_COLUMN` | `Result` | Label column (phishing vs. legitimate) |
| `PIPELINE_NAME` | `NetworkSecurity` | Pipeline identifier |
| `ARTIFACT_DIR` | `Artifacts` | Root output directory per run |
| `FILE_NAME` | `phisingData.csv` | Raw dataset filename |
| `SCHEMA_FILE_PATH` | `data_schema/schema.yaml` | Expected schema (31 columns) |
| `SAVED_MODEL_DIR` | `saved_models` | Long-term model storage |
| `DATA_INGESTION_COLLECTION_NAME` | `NetworkData` | MongoDB collection |
| `DATA_INGESTION_DATABASE_NAME` | `SegunMichael` | MongoDB database |
| `DATA_INGESTED_TRAIN_TEST_SPLIT_RATION` | `0.2` | Test split size |
| `DATA_TRANSFORMATION_IMPUTER_PARAMS` | `n_neighbors=3, weights='uniform'` | KNN imputation settings |
| `MODEL_TRAINER_EXPECTED_SCORE` | `0.6` | Minimum acceptable model score |
| `MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD` | `0.05` | Max allowed train/test score gap |
| `TRAINING_BUCKET_NAME` | `netwworksecurity0` | AWS S3 bucket for training assets |

---

## 5. Artifacts Produced Per Run

Each pipeline execution creates a timestamped run directory, e.g. `Artifacts/07_11_2026_03_38_43/`, containing:

```
Artifacts/<timestamp>/
├── data ingestion/
│   └── ingested/
│       ├── train.csv
│       └── test.csv
├── data_validation/
│   ├── validation/ | invalid/
│   └── drift_report/report.yaml
├── data_transformation/
│   ├── transformed/            # transformed train/test arrays
│   └── transformed_object/     # preprocessing.pkl
└── model_trainer/
    └── trained_model/
        └── model.pkl
```

Supporting top-level folders: `Network_Data/` (raw data), `valid_data/` (validated data), `final_model/` (promoted model + preprocessor), `prediction_output/` (batch/API prediction results), `templates/` (FastAPI HTML views).

---

## 6. Model Results

Multiple candidate algorithms were trained and logged to MLflow/DagsHub. Metrics below are from the tracked experiment runs.

### 🏆 Best / Winning Model: Random Forest

| Metric | Score |
|---|---|
| F1 Score | 0.9920 |
| Precision | 0.9899 |
| Recall | 0.9941 |

This is the model promoted to `final_model/` and served in production.

### Reference run (earlier candidate, logged for comparison)

| Split | F1 Score | Precision | Recall |
|---|---|---|---|
| Train | 0.9923 | 0.9901 | 0.9945 |
| Test | 0.9714 | 0.9630 | 0.9800 |

The Random Forest model outperformed this candidate on the test set while maintaining a healthy train/test gap — well within the overfitting/underfitting threshold defined in the config (0.05) — making it the selected production model.

**Experiment tracking:** all runs (params, metrics, artifacts) are logged via the DagsHub + MLflow integration and viewable at the project's DagsHub repository under `Michael-Segun/Networksecurity`.

---

## 7. Project Structure

```
Networksecurity/
├── .github/workflows/          # CI/CD pipeline (GitHub Actions)
├── Network_Data/                # Raw source data
├── data_schema/schema.yaml      # Expected data schema
├── final_model/                 # Production-selected model + preprocessor
├── networksecurity/             # Core Python package (pipeline components, utils, entities)
├── prediction_output/           # Saved prediction results
├── templates/                   # FastAPI Jinja2 HTML templates
├── valid_data/                  # Schema-validated data
├── app.py                       # FastAPI application (serving + training trigger endpoints)
├── main.py                      # Pipeline orchestration entry point
├── push_data.py                 # Script to push raw CSV data into MongoDB
├── test_mongo_db.py             # MongoDB connectivity test
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup (editable install)
└── mlflow.db                    # Local MLflow tracking store
```

---

## 8. How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Michael-Segun/Networksecurity.git
cd Networksecurity

# 2. Create environment & install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment variables (.env)
#    MONGO_DB_URL=
#    AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION

# 4. Push raw data to MongoDB (one-time)
python push_data.py

# 5. Run the full training pipeline
python main.py

# 6. Launch the API
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### Run with Docker

```bash
docker build -t networksecurity .
docker run -d -p 8080:8080 --name networksecurity networksecurity
```

---

## 9. Deployment Architecture (CI/CD)

```
git push (main)
      │
      ▼
GitHub Actions: Continuous Integration
      (lint + tests)
      │
      ▼
GitHub Actions: Continuous Delivery
      (docker build → push to AWS ECR)
      │
      ▼
GitHub Actions: Continuous Deployment
      (self-hosted EC2 runner pulls image → runs container on port 8080)
```

This mirrors a standard production MLOps deployment loop: every merge to `main` is automatically tested, containerized, versioned in a registry, and rolled out — no manual server access required.

---

## 10. Possible Future Improvements

- Add automated data/model drift monitoring in production (not just at validation time).
- Expand the CI pipeline with real unit/integration tests (currently placeholder echo steps).
- Add a model registry stage gate (e.g., MLflow Model Registry stages: Staging → Production).
- Add authentication and rate-limiting to the FastAPI prediction endpoint.
- A/B test candidate models before full promotion.

---

## Author

**Michael Segun** ([@Michael-Segun](https://github.com/Michael-Segun)) — Data Analyst / ML Practitioner focused on agentic AI and applied ML systems.