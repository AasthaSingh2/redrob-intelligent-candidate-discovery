# Redrob Intelligent Candidate Discovery

An explainable AI-powered candidate ranking system built for the **Redrob Data & AI Challenge**.

The system ranks 100,000 candidate profiles against a Senior AI/ML Retrieval Engineer Job Description using a multi-dimensional scoring engine instead of simple keyword matching.

---

# Overview

Traditional keyword search cannot distinguish between:

- An HR Manager with AI keywords
- A real ML Engineer with production retrieval experience

This project solves that problem using an explainable hybrid ranking algorithm that evaluates:

- Role fit
- Skill depth
- Career quality
- Education
- Behavioral signals
- Location preference

Each candidate receives:

- Final ranking score
- Rank
- Human-readable reasoning explaining why they were selected

---

# System Workflow

Candidate JSON
       │
       ▼
Feature Extraction
       │
       ▼
6-Dimensional Scoring
       │
       ▼
Availability Multiplier
       │
       ▼
Honeypot Detection
       │
       ▼
Top 100 Ranked Candidates
       │
       ▼
CSV/XLSX Output

---

# Dataset

Input:

- candidates.jsonl
- 100,000 candidate profiles

Each profile contains:

- Profile information
- Skills
- Career history
- Education
- Redrob behavioral signals

Output:

Top 100 ranked candidates in CSV/XLSX format.

---


# Scoring Architecture

The ranking engine combines multiple scoring dimensions.

| Component | Weight |
|-----------|--------|
| Title & Role Fit | 20% |
| Skill Depth | 24% |
| Career Quality | 28% |
| Education | 5% |
| Behavioral Signals | 18% |
| Location Preference | 5% |

The final score is multiplied by an **Availability Multiplier**, ensuring inactive candidates do not rank highly.

Final Score = Base Score × Availability Multiplier

---

# Candidate Evaluation

## 1. Title Fit

The algorithm first checks whether the candidate is actually suitable for the role.

Preferred titles include:

- Machine Learning Engineer
- AI Engineer
- NLP Engineer
- Search Engineer
- Recommendation Systems Engineer
- Applied Scientist

Wrong roles such as HR Manager, Accountant, Marketing Manager, Frontend Developer, etc. receive a heavy penalty.

---

## 2. Skill Depth

Instead of counting keywords, every skill receives a depth score based on:

- proficiency level
- endorsements
- months of experience

Important skills include:

- FAISS
- Pinecone
- Weaviate
- Qdrant
- Milvus
- Elasticsearch
- OpenSearch
- Semantic Search
- Embeddings
- Ranking
- Retrieval
- Python
- Learning to Rank

Keyword stuffing is automatically penalized.

---

## 3. Career Quality

Career quality evaluates:

- Production AI systems
- Tier-1 product companies
- Quantified impact
- Recommendation systems
- Search systems
- Retrieval pipelines
- RAG implementations
- AI project descriptions
- Years of experience
- Job stability

Candidates with real production ML experience receive significantly higher scores.

---

## 4. Education

Education contributes a small score based on:

- Institute tier
- Degree
- Field of study

Because the Job Description focuses primarily on experience, education has a low overall weight.

---

## 5. Behavioral Signals

Behavioral signals measure hireability rather than technical ability.

Signals include:

- Open to Work
- Recruiter response rate
- Last active date
- GitHub activity
- Interview completion
- Profile completeness
- Skill assessments
- Notice period

These are combined into an Availability Multiplier.

---

## 6. Location Preference

Candidates located in preferred hiring cities receive additional score.

Preferred locations include:

- Bengaluru
- Hyderabad
- Pune
- Noida
- Gurugram
- Mumbai
- Delhi

Candidates willing to relocate receive partial credit.

---

# Availability Multiplier

Strong candidates who are inactive should not rank above active candidates.

Availability is calculated using:

- Last active date
- Open-to-work status
- Recruiter response rate

This multiplier reduces scores for inactive candidates.

---

# Honeypot Detection

The ranker explicitly detects misleading candidate profiles.

Examples include:

- Keyword stuffing
- Impossible skill combinations
- Expert skills with zero experience
- Ghost candidates
- Wrong job titles
- Wrong technical domain

Detected honeypots receive large penalties or near-zero scores.

---

# Explainable Ranking

Each selected candidate includes a generated explanation summarizing:

- Current role
- Company
- Years of experience
- Relevant AI work
- Production achievements
- Recruiter responsiveness
- Availability

Example:

> Built a RAG-based ranking pipeline serving 50M+ queries/month at Razorpay (6.7 years as Lead AI Engineer). Open to work, 73% recruiter response rate, active recently.

---

# Project Structure

```
redrob-submission/

│
├── candidates.jsonl
├── rank.py
├── validate_submission.py
├── my_team.csv
└── README.md
```

---

# How to Run

Run the ranking algorithm:

```bash
python rank.py --candidates candidates.jsonl --out my_team.csv
```

Validate the submission:

```bash
python validate_submission.py my_team.csv
```

Expected output:

```
Submission is valid.
```

---

# Output Format

The generated CSV contains:

| candidate_id | rank | score | reasoning |
|--------------|------|--------|-----------|

The top 100 candidates are sorted by descending score.

---

# Performance

- Dataset Size: 100,000 candidates
- Runtime: ~3–4 minutes (CPU)
- Dependencies: Python Standard Library only
- Internet Required: No
- GPU Required: No

---

# Features

- Explainable candidate ranking
- Hybrid scoring model
- Production-aware career evaluation
- Skill depth analysis
- Behavioral signal integration
- Honeypot detection
- Availability-aware ranking
- Offline execution
- Validator compatible output

---

# Submission

This repository contains:

- Source code
- Ranking algorithm
- Submission output
- Documentation

Prepared for the **Redrob Data & AI Challenge**.

## - AASTHA SINGH 
