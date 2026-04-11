# SkillIQ — Transformer Model Guide

## Model Choice: DistilBERT

**Model:** `distilbert-base-uncased`  
**Task:** Multi-label skill classification from resume/profile/marksheet text  
**Domain:** Computer Science & Engineering (CSE)

### Why DistilBERT?

| Factor | DistilBERT | BERT-base | RoBERTa |
|--------|-----------|-----------|---------|
| Size | 66M params | 110M | 125M |
| Speed | 60% faster | Baseline | Slower |
| Accuracy | 97% of BERT | 100% | 105% |
| RAM (CPU) | ~500MB | ~900MB | ~1GB |
| Best for | Production, limited hardware | Research | High accuracy needs |

DistilBERT is the **optimal choice** for SkillIQ because:
- Students run this on laptops/modest servers
- Resume texts are short (200-500 words) — BERT's full capacity is overkill
- 97% accuracy retention with 40% size reduction is an excellent trade-off

## Setup

```bash
pip install transformers torch datasets accelerate
python scripts/train_cse_transformer.py
```

## What It Detects (26 skill labels)

**Core CSE:** python, java, c++, data_structures, algorithms, dbms, sql, operating_systems, computer_networks, oop, git, debugging, testing, web_development, api_development, system_design, cloud_fundamentals, linux

**Government Jobs:** quantitative_aptitude, reasoning, english_communication, current_affairs

**Study Abroad:** research_methodology, sop_writing, ielts_toefl

**Universal:** team_collaboration

## Training Data

The model is trained on 70+ synthetic CSE student profiles covering:
- Government exam aspirants (GATE, ISRO, SSC)
- IT job seekers (SWE, Backend, QA, DevOps)
- Study abroad applicants (MS CS, MS DS, PhD)

**For production:** Replace/augment with real anonymized student data labeled by domain experts.

## Integration with Backend

```python
from scripts.train_cse_transformer import load_and_predict

# After training:
skills = load_and_predict("B.Tech CSE 8.5 CGPA. Python, Django, REST APIs...")
# Returns: ['python', 'api_development', 'dbms', 'data_structures', ...]
```

The backend `app/cse_career.py` uses keyword-based detection by default.
After training, replace `detect_skills_from_text()` with `load_and_predict()` for
transformer-powered detection.

## Model Artifacts

After training, files are saved to:
```
model_artifacts/cse_skill_classifier/
  config.json
  pytorch_model.bin  (or model.safetensors)
  tokenizer.json
  tokenizer_config.json
  vocab.txt
  training_report.json  ← F1, precision, recall metrics
```
