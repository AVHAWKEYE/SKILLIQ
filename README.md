# SkillIQ

SkillIQ is now a complete working project with:

- Assessment web app (existing UI)
- FastAPI backend
- SQLite database for assessment storage
- Built-in model training pipeline
- Prediction API
- Assessment labeling flow so the model gets trainable data

## Project Structure

```
skilliq/
├── server.py
├── css/
├── js/
├── index.html
├── requirements.txt
└── README.md
```

## Run Locally (Windows PowerShell)

```powershell
cd P:\SkillIQ
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\server.py
```

Open http://127.0.0.1:8000

## Model Data Workflow

1. Complete an assessment in the UI.
2. Assessment summary is auto-saved to database as a record.
3. Enter a known target score (for example real exam score) and click Save Label.
4. After enough labeled records, click Train Model.
5. Use Predict to estimate target score from latest assessment features.

Training requires at least 12 labeled records.

## Train With Kaggle CSV Data

You can bulk-import Kaggle rows and retrain the model in one command.

1. Put your Kaggle CSV in this project folder (or use an absolute path).
2. Copy `kaggle_column_map.example.json` to a new file, for example `kaggle_column_map.json`.
3. Update the `fields` mapping so each SkillIQ field points to your Kaggle column name.
4. Run import + train:

```powershell
cd P:\SkillIQ
.\.venv\Scripts\python.exe .\scripts\kaggle_import.py --csv .\your_kaggle_data.csv --map .\kaggle_column_map.json --train
```

Useful flags:

- `--fail-on-row-error` to stop at first bad row.
- `--delimiter ';'` if your CSV uses semicolons.

What the script does:

- Converts Kaggle rows into SkillIQ schema.
- Validates each row using the same constraints as the API.
- Inserts valid rows into `skilliq.db`.
- Trains and writes `model_artifacts/linear_model.json` when `--train` is used.

You can also import directly from the UI on the assessment completion screen:

- Select CSV file
- Select mapping JSON file
- Click `Import + Train`

## Kaggle Upload API

Endpoint: `POST /api/import-kaggle`

Multipart form fields:

- `csv_file` (required): Kaggle CSV file.
- `mapping_file` (required): JSON mapping file.
- `train` (optional): `true` to train after import.
- `delimiter` (optional): CSV delimiter, default `,`.
- `fail_on_row_error` (optional): `true` to abort on first bad row.

## External Model Prediction API

Endpoint: `POST /api/external/predict`

Supports two request styles:

- Send external model features directly:
	- `attendance_percentage`
	- `quiz_average`
	- `assignment_average`
	- `midterm_score`
	- `participation_score`
	- `study_hours_per_week`
	- `previous_gpa`
- Or send a normal SkillIQ payload (same fields as `/api/predict`), and backend will derive external features automatically.

Response includes:

- `predicted_score` (from `score_predictor.json`)
- `risk_assessment` label + class probabilities (from `risk_assessor.json`)
- `grade_classification` grade + class probabilities (from `grade_classifier.json`)

UI integration:

- Use `Predict (External)` button on assessment completion card.

## Added Dataset Profiles

This project now includes two ready-to-run dataset preparation scripts:

- `scripts/prepare_student_performance_dataset.py` for `student-mat.csv` style data.
- `scripts/prepare_student_performance_10k.py` for `Student_performance_10k.csv` style data.

Example for the 10k CSV:

```powershell
cd P:\SkillIQ
c:/python314/python.exe .\scripts\prepare_student_performance_10k.py --input "C:\Users\Parre Pratyush\Downloads\archive (1)\Student_performance_10k.csv" --output .\data\student_performance_10k_skilliq.csv
c:/python314/python.exe .\scripts\kaggle_import.py --csv .\data\student_performance_10k_skilliq.csv --map .\kaggle_column_map.student_performance.json --train
```

## External Model Artifacts

Attached model files can be stored under:

- `model_artifacts/external_models/`

Use API endpoint `GET /api/external-models` to list synced JSON/PKL artifacts and file details.

## API Endpoints

- `GET /api/health`
- `POST /api/assessments`
- `GET /api/assessments`
- `PATCH /api/assessments/{assessment_id}/label`
- `POST /api/train`
- `POST /api/predict`

## Notes

- Database file: `skilliq.db`
- Trained model artifact: `model_artifacts/linear_model.json`
- Existing AI insights and plan calls in the frontend remain unchanged.
