Overview

Redrob Intelligent Candidate Discovery is an explainable AI-powered ranking engine designed to recommend the Top 100 candidates from a pool of 100,000 profiles for a Senior AI Engineer role.

Instead of relying solely on keyword matching, the engine evaluates candidates using recruiter-inspired reasoning across multiple dimensions including technical skills, production experience, behavioral signals, education, role fit, and hiring readiness.

The entire solution is implemented using only the Python Standard Library and executes completely offline, satisfying all challenge constraints.

Problem Statement

Traditional resume search systems struggle to identify genuinely qualified candidates because they primarily rely on exact keyword matching.

For example:

❌ A frontend developer who casually lists "FAISS" or "Pinecone" may appear highly relevant.

Meanwhile,

✅ A Senior Machine Learning Engineer who actually built production retrieval systems may rank lower simply because specific keywords are missing.

This project addresses that challenge through a hybrid scoring engine that evaluates candidates the way an experienced recruiter would.

Key Features
Rank 100,000 candidate profiles efficiently
Fully explainable scoring engine
Multi-dimensional candidate evaluation
Production experience detection
Behavioral signal analysis
Title-aware candidate ranking
Availability-aware scoring
Honeypot profile detection
Human-readable reasoning for every ranked candidate
Pure Python Standard Library implementation
Offline execution (No Internet, No GPU)
System Workflow
Candidate Profiles (.jsonl / .jsonl.gz)
                │
                ▼
      Feature Extraction Engine
                │
                ▼
     Multi-Dimensional Scoring
                │
                ▼
          Title Gate
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
       CSV Submission
Scoring Architecture

The final ranking score is computed as:

Final Score = Base Score × Title Gate × Availability Multiplier

where

Title Gate = 0.15 + 0.85 × Title Score

Availability Multiplier = 0.75 + 0.25 × Availability Score

This design ensures that:

Wrong-role candidates are heavily suppressed.
Strong but slightly inactive candidates are down-weighted rather than eliminated.
Candidate Evaluation Dimensions
Component	Weight	Description
Career Quality	30%	Production systems, company quality, measurable impact
Skill Depth	22%	Technical expertise, endorsements, duration
Behavioral Signals	20%	Recruiter engagement and hiring readiness
Title Fit	18%	Alignment with Senior AI Engineer role
Education	3%	Institution, degree, specialization
Location	2%	Preferred hiring locations
Career Quality

The engine evaluates career history using:

Production deployment evidence
Large-scale system ownership
Search and retrieval experience
Recommendation systems
Quantified business impact
Company quality
Years of experience
Career stability

Rather than counting keywords, it searches for meaningful engineering signals throughout the candidate's work history.

Skill Evaluation

Skills are evaluated using three factors:

Skill Depth =
50% Proficiency
25% Endorsements
25% Experience Duration

Important technical areas include:

Retrieval Systems
Semantic Search
Vector Databases
Ranking Systems
Recommendation Systems
Python
Evaluation Metrics
Retrieval-Augmented Generation (RAG)
Behavioral Signals

The ranking engine considers hiring readiness using recruiter signals such as:

Recruiter response rate
Profile recency
Interview completion rate
Notice period
GitHub activity
Profile completeness
Open-to-work status
Recruiter saves

These signals help prioritize candidates who are both technically strong and realistically available.

Honeypot Detection

The engine detects suspicious profiles by identifying patterns such as:

Expert skills with zero experience duration
Multiple expert-level skills without endorsements
Unrealistic combinations of unrelated technical stacks

Detected honeypot profiles receive a near-zero score and are excluded from the final ranking.

Explainable Reasoning

Each recommended candidate includes a concise explanation generated from their actual profile.

Example:

Built a production semantic search platform serving millions of users at a leading product company. Strong retrieval experience with FAISS and Pinecone. Open to work with a 30-day notice period.

This makes every ranking transparent and recruiter-friendly.

Performance
Metric	Value
Candidate Pool	100,000
Runtime	~4 minutes
Internet Required	No
GPU Required	No
Dependencies	None
Validation	✅ Passed
Project Structure
redrob-intelligent-candidate-discovery/
│
├── rank.py
├── validate_submission.py
├── README.md
├── requirements.txt
├── LICENSE
│
├── docs/
│   └── Redrob_Candidate_Discovery.pdf
│
Running the Project
python rank.py --candidates candidates.jsonl --out my_team.csv

Validate the submission:

python validate_submission.py my_team.csv

Expected output:

Submission is valid.
Future Improvements

Potential enhancements include:

Learning-to-Rank models
LLM-assisted reranking
Interactive recruiter dashboard
Real-time multi-job ranking
Feedback-driven learning
Resume parsing from PDF documents
Author

Aastha Singh

Developed for the Redrob Data & AI Challenge – Intelligent Candidate Discovery.
