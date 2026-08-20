# Deployment Guide

## Local Installation

Clone the repository:

```powershell
git clone https://github.com/amancs01/phishing-url-detection.git
cd phishing-url-detection
```

Create a virtual environment:

```powershell
python -m venv .venv
```

## Environment Setup

Normal PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by PowerShell execution policy, do not change the
policy. Use the virtual-environment Python interpreter directly:

```powershell
.\.venv\Scripts\python.exe --version
```

## Dependency Installation

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Dataset Reproduction

The packaged dashboard can run from the committed optimized model. To
reproduce the dataset workflow locally:

```powershell
.\.venv\Scripts\python.exe -m src.download_data
.\.venv\Scripts\python.exe -m src.inspect_data
.\.venv\Scripts\python.exe -m src.validate_data
.\.venv\Scripts\python.exe -m src.prepare_data
.\.venv\Scripts\python.exe -m src.split_data
```

Raw and processed full datasets are intentionally ignored by Git.

## Model Reproduction

After preparing and splitting data, reproduce the model workflow:

```powershell
.\.venv\Scripts\python.exe -m src.train_baseline
.\.venv\Scripts\python.exe -m src.tune_model
.\.venv\Scripts\python.exe -m src.analyze_pruning
.\.venv\Scripts\python.exe -m src.select_model
.\.venv\Scripts\python.exe -m src.evaluate_final
.\.venv\Scripts\python.exe -m src.model_interpretation
```

The final dashboard loads:

```text
models/optimized_decision_tree.joblib
```

## Dashboard Startup

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard analyses only URL text and does not contact submitted websites.

## Streamlit Community Cloud Deployment

Normal deployment process:

1. Push the repository to GitHub.
2. Ensure `requirements.txt` is present.
3. Ensure `app.py` is the Streamlit entry point.
4. Ensure `models/optimized_decision_tree.joblib` is committed.
5. Connect the GitHub repository in Streamlit Community Cloud.
6. Select `app.py` as the main file.
7. Deploy.

No deployed URL is listed here because deployment has not been performed in
this repository.

## Troubleshooting

### Missing Model

If the dashboard says the optimized model is missing, confirm this file exists:

```text
models/optimized_decision_tree.joblib
```

If reproducing locally, run:

```powershell
.\.venv\Scripts\python.exe -m src.select_model
```

### Missing Package

Install dependencies again:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Python Interpreter Mismatch

Check the interpreter:

```powershell
.\.venv\Scripts\python.exe --version
```

Use the same interpreter for scripts, tests, and Streamlit.

### PowerShell Activation Restriction

If activation is blocked, run commands through:

```powershell
.\.venv\Scripts\python.exe
```

Do not change Windows execution policy just for this project.
