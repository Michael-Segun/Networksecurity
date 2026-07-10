🛡️ NetworkSecurity — Phishing Website Detection (End-to-End MLOps Pipeline)
============================================================================

> An end-to-end, production-style **MLOps pipeline** that ingests raw website/URL feature data, validates and transforms it, trains and evaluates a classifier, tracks every experiment, and ships the winning model as a containerized, CI/CD-deployed prediction API.

Repository: [github.com/Michael-Segun/Networksecurity](https://github.com/Michael-Segun/Networksecurity)

1\. Problem Statement
---------------------

Phishing websites imitate legitimate ones to steal credentials, financial information, and personal data. Manually blacklisting URLs doesn't scale — new phishing domains appear constantly, and static blocklists always lag behind attackers.

**This project solves that problem by framing phishing detection as a supervised binary classification task.** Given a set of structural, lexical, and behavioral features extracted from a website/URL (e.g., URL length, use of IP address, presence of @ symbol, SSL certificate status, domain age, abnormal redirects, iframe usage, etc.), the model predicts whether the site is:

*   **Legitimate (safe)**, or
    
*   **Phishing (malicious)**
    

The goal is not just a notebook with a good F1 score — it's a **repeatable, monitorable, and deployable pipeline** that mirrors how this kind of model would actually be operated in a real security product: data lands in a database → gets validated against a schema → gets transformed → a model gets trained, evaluated, and versioned → the best model is packaged and shipped to production behind an API.

### Industries this project is relevant to

*   **Cybersecurity vendors & SOC/SIEM platforms** — real-time URL/domain reputation scoring as a threat-intel feature.
    
*   **Banking, Fintech & Payments** — protecting customers from phishing pages that spoof login/checkout flows.
    
*   **Email Security & Gateways** — scanning links in inbound email before they reach a user's inbox.
    
*   **Telecom & ISPs** — network-level filtering of malicious domains at the DNS/gateway layer.
    
*   **E-commerce & Retail** — brand protection against fake storefronts and checkout clones.
    
*   **Browser vendors & Endpoint Security** — powering "Safe Browsing"-style warnings.
    
*   **Government & Critical Infrastructure** — securing citizen-facing portals and internal networks.
    

2\. Tech Stack & Tools
----------------------

LayerTools / LibrariesLanguagePythonData storageMongoDB (pymongo, pymongo\[srv\])Data sciencepandas, numpy, scikit-learnMissing value handlingKNNImputer (scikit-learn)Experiment tracking**MLflow**, hosted/remote-tracked via **DagsHub**Serializationdill (models/preprocessors), pyaml/YAML (schema & reports)API serving**FastAPI** + **Uvicorn**, python-multipartConfig/secretspython-dotenvContainerization**Docker**Cloud**AWS** — S3 (training bucket), **ECR** (image registry), **EC2** (self-hosted runner / serving host)CI/CD**GitHub Actions** (3-stage: Integration → Build & Push to ECR → Continuous Deployment on self-hosted EC2 runner)Templating (API UI)Jinja2 templates/ (HTML, served via FastAPI)

3\. Project Architecture — Pipeline Stages
------------------------------------------

The pipeline follows a modular, config-driven ML pipeline architecture (networksecurity/ package), where every run produces a timestamped, versioned Artifacts/ directory. This mirrors industry-standard pipelines used in production ML systems (à la Kubeflow/TFX-style staged pipelines, just self-orchestrated in Python).

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Raw Data (MongoDB)         │        ▼  [1] Data Ingestion         │  → train.csv / test.csv        ▼  [2] Data Validation         │  → schema check + drift report        ▼  [3] Data Transformation         │  → KNN-imputed, transformed feature arrays + preprocessor.pkl        ▼  [4] Model Trainer         │  → trained model + train/test metrics        ▼  [5] Model Evaluation & Registry (MLflow via DagsHub)        │        ▼  [6] Packaging (final_model/) → Docker Image → ECR → EC2 → FastAPI serving   `

Each stage below follows the same three-part contract used throughout the pipeline: **Config** (what drives its behavior), **Component** (what the stage actually does), and **Artifact** (what it hands off to the next stage).

### Stage 1 — Data Ingestion

**Config**

ConstantValueDATA\_INGESTION\_COLLECTION\_NAMENetworkDataDATA\_INGESTION\_DATABASE\_NAMESegunMichaelDATA\_INGESTION\_DIR\_NAMEdata ingestionDATA\_INGESTION\_FEATURE\_STORE\_DIRfeature\_storeDATA\_INGESTION\_INGESTED\_DIRingestedDATA\_INGESTED\_TRAIN\_TEST\_SPLIT\_RATION0.2

**Component**

*   Data\_Ingestion class connects to **MongoDB**, pulls the NetworkData collection from the SegunMichael database into a Pandas DataFrame.
    
*   The raw pull is exported to a **feature store** directory (an untouched snapshot of what came out of Mongo, kept separate from the split files so the original pull stays traceable).
    
*   A **train/test split** (split\_data\_as\_train\_test) is then performed using the 0.2 ratio, and both splits are exported to the ingested/ folder.
    

**Artifact**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   DataIngestionArtifact(      trained_file_path='Artifacts//data ingestion/ingested/train.csv',      test_file_path='Artifacts//data ingestion/ingested/test.csv'  )   `

This artifact is what gets passed into Data Validation — the next stage never touches MongoDB or the feature store directly, only these two file paths.

### Stage 2 — Data Validation

**Config**

ConstantValueDATA\_VALIDATION\_DIR\_NAMEdata\_validationDATA\_VALIDATION\_VALID\_DIRvalidationDATA\_VALIDATION\_INVALID\_DIRinvalidDATA\_VALIDATION\_DRIFT\_REPORT\_DIRdrift\_reportDATA\_VALIDATION\_DRIFT\_REPORT\_FILE\_NAMEreport.yamlSCHEMA\_FILE\_PATHdata\_schema/schema.yaml

**Component**

*   **Purpose**: guard the pipeline from silently training on malformed, incomplete, or drifted data — a standard MLOps safeguard sitting between ingestion and transformation.
    
*   **Schema check**: the ingested train/test DataFrames are validated against data\_schema/schema.yaml, confirming the expected column count (**31 columns**) is present before proceeding. A mismatch routes the data to invalid/ instead of letting it continue downstream.
    
*   **Data drift detection**: this is the stage where the **drift report is generated**. Train and test distributions are statistically compared column-by-column, and the results — including whether drift was detected per feature — are written to a structured **report.yaml** under drift\_report/. This gives an auditable, versioned record of whether the held-out test set still reflects the training distribution, which is essential for catching data quality issues before they silently degrade model performance downstream.
    
*   Data passing both checks is written to validation/; anything failing is isolated in invalid/.
    

**Artifact**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   DataValidationArtifact(      validation_status=True/False,      valid_train_file_path='Artifacts//data_validation/validation/train.csv',      valid_test_file_path='Artifacts//data_validation/validation/test.csv',      invalid_train_file_path=...,      invalid_test_file_path=...,      drift_report_file_path='Artifacts//data_validation/drift_report/report.yaml'  )   `

### Stage 3 — Data Transformation

**Config**

ConstantValueDATA\_TRANSFORMATION\_DIR\_NAMEdata\_transformationDATA\_TRANSFORMATION\_TRANSFORMED\_DATA\_DIRtransformedDATA\_TRANSFORMATION\_TRANSFORMED\_OBJECT\_DIRtransformed\_objectDATA\_TRANSFORMATION\_IMPUTER\_PARAMS{missing\_values: nan, n\_neighbors: 3, weights: 'uniform'}PREPROCESSING\_OBJECT\_FILE\_NAMEpreprocessing.pklTARGET\_COLUMNResult

**Component**

*   DataTransformation class, entry point initiate\_data\_transformation().
    
*   get\_data\_transformer\_object() builds a preprocessing pipeline centered on a **KNNImputer** (n\_neighbors=3, weights='uniform') to fill missing feature values.
    
*   The imputer is **fit on the training split only**, then used to transform() both train and test splits — standard practice to prevent test-set leakage into the imputation logic.
    
*   The target column (Result) is separated from the feature matrix before transformation and re-attached afterward.
    
*   The transformed feature matrices are converted to **NumPy arrays and saved as .npy files (not CSV)**. This is a deliberate choice at this stage — .npy preserves exact dtypes and loads considerably faster than CSV for the model training step that follows immediately after, since no re-parsing or type inference is needed.
    
*   The fitted imputer/preprocessor object is serialized separately via MainUtils.save\_object() as preprocessing.pkl, so the exact same transformation can be re-applied at inference time in production (this is the object later shipped inside final\_model/).
    

**Artifact**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   DataTransformationArtifact(      transformed_object_file_path='Artifacts//data_transformation/transformed_object/preprocessing.pkl',      transformed_train_file_path='Artifacts//data_transformation/transformed/train.npy',      transformed_test_file_path='Artifacts//data_transformation/transformed/test.npy'  )   `

### Stage 4 — Model Trainer

**Config**

ConstantValueMODEL\_TRAINER\_DIR\_NAMEmodel\_trainerMODEL\_TRAINER\_TRAINED\_MODEL\_DIRtrained\_modelMODEL\_TRAINER\_TRAINED\_MODEL\_NAMEmodel.pklMODEL\_TRAINER\_EXPECTED\_SCORE0.6MODEL\_TRAINER\_OVER\_FIITING\_UNDER\_FITTING\_THRESHOLD0.05

**Component**

*   Loads the transformed .npy train/test arrays produced in Stage 3 (fast load, no re-parsing needed).
    
*   Trains and compares multiple candidate classifiers, scoring each on **F1, Precision, and Recall** across both train and test splits.
    
*   Applies two gates before accepting a model:
    
    1.  **Minimum performance gate** — test score must exceed MODEL\_TRAINER\_EXPECTED\_SCORE (0.6).
        
    2.  **Overfitting/underfitting gate** — the gap between train and test scores must stay within MODEL\_TRAINER\_OVER\_FIITING\_UNDER\_FITTING\_THRESHOLD (0.05), rejecting models that memorize the training set.
        
*   The winning model (**Random Forest**) and its fitted preprocessor are serialized together via MainUtils.save\_object() as model.pk.
    
*   **Experiment tracking**: every run's parameters, metrics, and model artifact are logged to **MLflow**, tracked remotely through **DagsHub** (Michael-Segun/Networksecurity repo), giving a permanent, comparable history of every training run.
    

**Artifact**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   ModelTrainerArtifact(      trained_model_file_path='Artifacts//model_trainer/trained_model/model.pk',      train_metric_artifact=ClassificationMetricArtifact(f1_score=..., precision_score=..., recall_score=...),      test_metric_artifact=ClassificationMetricArtifact(f1_score=..., precision_score=..., recall_score=...)  )   `

### Stage 5 — Model Evaluation & Registry

*   All runs are visible and comparable on the **DagsHub MLflow UI**, enabling side-by-side comparison of algorithms and hyperparameters before promoting a model to final\_model/.
    
*   The Random Forest run above was the one promoted — it cleared both the performance and overfitting gates from Stage 4 with the best test-set F1/Precision/Recall of all logged runs.
    

### Stage 6 — Packaging, CI/CD & Serving

*   **final\_model/** holds the production-selected model + preprocessor.
    
*   **app.py** — FastAPI application serving predictions (with Jinja2 templates/ for a simple web UI) and writing results to prediction\_output/.
    
*   **Dockerfile** — containerizes the app for deployment.
    
*   **CI/CD (.github/workflows)** — 3-job GitHub Actions pipeline:
    
    1.  **Continuous Integration** — checkout, lint, unit tests.
        
    2.  **Continuous Delivery** — builds the Docker image and pushes it to **AWS ECR**.
        
    3.  **Continuous Deployment** — a **self-hosted runner on EC2** pulls the latest ECR image and runs it (docker run -d -p 8080:8080 ...), with AWS credentials injected as environment variables and old images pruned automatically.
        

4\. Configuration Reference (training\_pipeline constants)
----------------------------------------------------------

ConstantValuePurposeTARGET\_COLUMNResultLabel column (phishing vs. legitimate)PIPELINE\_NAMENetworkSecurityPipeline identifierARTIFACT\_DIRArtifactsRoot output directory per runFILE\_NAMEphisingData.csvRaw dataset filenameSCHEMA\_FILE\_PATHdata\_schema/schema.yamlExpected schema (31 columns)SAVED\_MODEL\_DIRsaved\_modelsLong-term model storageDATA\_INGESTION\_COLLECTION\_NAMENetworkDataMongoDB collectionDATA\_INGESTION\_DATABASE\_NAMESegunMichaelMongoDB databaseDATA\_INGESTED\_TRAIN\_TEST\_SPLIT\_RATION0.2Test split sizeDATA\_TRANSFORMATION\_IMPUTER\_PARAMSn\_neighbors=3, weights='uniform'KNN imputation settingsMODEL\_TRAINER\_EXPECTED\_SCORE0.6Minimum acceptable model scoreMODEL\_TRAINER\_OVER\_FIITING\_UNDER\_FITTING\_THRESHOLD0.05Max allowed train/test score gapTRAINING\_BUCKET\_NAMEnetwworksecurity0AWS S3 bucket for training assets

5\. Artifacts Produced Per Run
------------------------------

Each pipeline execution creates a timestamped run directory, e.g. Artifacts/07\_11\_2026\_03\_38\_43/, containing:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Artifacts//  ├── data ingestion/  │   └── ingested/  │       ├── train.csv  │       └── test.csv  ├── data_validation/  │   ├── validation/ | invalid/  │   └── drift_report/report.yaml  ├── data_transformation/  │   ├── transformed/            # transformed train/test arrays  │   └── transformed_object/     # preprocessing.pkl  └── model_trainer/      └── trained_model/          └── model.pk   `

Supporting top-level folders: Network\_Data/ (raw data), valid\_data/ (validated data), final\_model/ (promoted model + preprocessor), prediction\_output/ (batch/API prediction results), templates/ (FastAPI HTML views).

6\. Model Results
-----------------

Multiple candidate algorithms were trained and logged to MLflow/DagsHub. Metrics below are from the tracked experiment runs.

### 🏆 Best / Winning Model: **Random Forest**

MetricScoreF1 Score**0.9920**Precision**0.9899**Recall**0.9941**

This is the model promoted to final\_model/ and served in production.

### Reference run (earlier candidate, logged for comparison)

SplitF1 ScorePrecisionRecallTrain0.99230.99010.9945Test0.97140.96300.9800

> The Random Forest model outperformed this candidate on the test set while maintaining a healthy train/test gap — well within the overfitting/underfitting threshold defined in the config (0.05) — making it the selected production model.

**Experiment tracking:** all runs (params, metrics, artifacts) are logged via dagshub+mlflow integration and viewable at the project's DagsHub repository under Michael-Segun/Networksecurity.

7\. Project Structure
---------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Networksecurity/  ├── .github/workflows/          # CI/CD pipeline (GitHub Actions)  ├── Network_Data/                # Raw source data  ├── data_schema/schema.yaml      # Expected data schema  ├── final_model/                 # Production-selected model + preprocessor  ├── networksecurity/              # Core Python package (pipeline components, utils, entities)  ├── prediction_output/            # Saved prediction results  ├── templates/                    # FastAPI Jinja2 HTML templates  ├── valid_data/                   # Schema-validated data  ├── app.py                        # FastAPI application (serving + training trigger endpoints)  ├── main.py                       # Pipeline orchestration entry point  ├── push_data.py                  # Script to push raw CSV data into MongoDB  ├── test_mongo_db.py               # MongoDB connectivity test  ├── Dockerfile                     # Container definition  ├── requirements.txt                # Python dependencies  ├── setup.py                        # Package setup (editable install)  └── mlflow.db                       # Local MLflow tracking store   `

8\. How to Run Locally
----------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # 1. Clone the repo  git clone https://github.com/Michael-Segun/Networksecurity.git  cd Networksecurity  # 2. Create environment & install dependencies  python -m venv venv  source venv/bin/activate        # Windows: venv\Scripts\activate  pip install -r requirements.txt  # 3. Configure environment variables (.env)  #    MONGO_DB_URL=  #    AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION  # 4. Push raw data to MongoDB (one-time)  python push_data.py  # 5. Run the full training pipeline  python main.py  # 6. Launch the API  uvicorn app:app --host 0.0.0.0 --port 8080 --reload   `

### Run with Docker

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   docker build -t networksecurity .  docker run -d -p 8080:8080 --name networksecurity networksecurity   `

9\. Deployment Architecture (CI/CD)
-----------------------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   git push (main)      │     ▼  GitHub Actions: Continuous Integration  (lint + tests)     │     ▼  GitHub Actions: Continuous Delivery     (docker build → push to AWS ECR)     │     ▼  GitHub Actions: Continuous Deployment   (self-hosted EC2 runner pulls image → runs container on port 8080)   `

This mirrors a standard production MLOps deployment loop: every merge to main is automatically tested, containerized, versioned in a registry, and rolled out — no manual server access required.

10\. Possible Future Improvements
---------------------------------

*   Add automated data/model drift monitoring in production (not just at validation time).
    
*   Expand the CI pipeline with real unit/integration tests (currently placeholder echo steps).
    
*   Add a model registry stage gate (e.g., MLflow Model Registry stages: Staging → Production).
    
*   Add authentication and rate-limiting to the FastAPI prediction endpoint.
    
*   A/B test candidate models before full promotion.
    

Author
------

**Michael Segun** ([@Michael-Segun](https://github.com/Michael-Segun)) — Data Analyst / ML Practitioner focused on agentic AI and applied ML systems.