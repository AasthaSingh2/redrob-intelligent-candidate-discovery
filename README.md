# Redrob Intelligent Candidate Discovery


AI-powered candidate ranking for the Redrob Data & AI Challenge.
Ranks 100,000 candidate profiles against a Senior AI Engineer JD — the way a great recruiter would, not a keyword filter.




# The Problem

Traditional keyword search cannot distinguish between:


An HR Manager who listed "FAISS" and "Pinecone" in their skills
A real ML Engineer who shipped a production RAG pipeline serving 50M+ queries/month


This project solves that using an explainable hybrid scoring engine that understands role fit, skill depth, career quality, behavioral availability, and semantic intent — not just keyword presence.


# How to Run

bash# Run the ranker (100K candidates, ~4 min on CPU, no GPU, no internet)
python rank.py --candidates candidates.jsonl --out my_team.csv

# Also works with gzipped input
python rank.py --candidates candidates.jsonl.gz --out my_team.csv

# Validate before submitting
python validate_submission.py my_team.csv
# → Submission is valid.

Requirements: Python 3.8+ standard library only. No pip install needed.


# Scoring Architecture (v3)

Final Score = Base Score × title_gate × availability_multiplier

Base Score = Career(30%) + Skills(22%) + Title(18%) + Behavior(20%) + Education(3%) + Location(2%)

title_gate         = 0.15 + 0.85 × title_score        ← suppresses wrong-role candidates
availability_mult  = 0.75 + 0.25 × availability_raw   ← down-weights, doesn't destroy

Scoring Dimensions

ComponentWeightWhat It MeasuresCareer Depth30%Company tier, production evidence, semantic search/ranking intent in descriptions, quantified impactSkill Depth22%Fuzzy-matched skills with depth score (proficiency × endorsements × duration)Title & Role Fit18%Correct ML/AI/NLP/Search title — also acts as a gate on total scoreBehavioral Signals20%Response rate, recency, GitHub activity, notice period, interview completionEducation3%Institution tier, degree level, field of studyLocation2%Preferred cities (Pune/Noida/Hyderabad/Bangalore/Mumbai/Delhi)


Key Design Decisions

1. Fuzzy Skill Matching (not exact set lookup)

python# Old (v1/v2): exact match — misses "Sentence-Transformers", "sentence_transformers"
if skill_name in RETRIEVAL_SKILLS:

# New (v3): substring match — catches all variants
def fuzzy_match(text, keywords):
    return any(kw in text.lower() for kw in keywords)

2. Semantic Intent Detection

Searches headline, summary, and all career descriptions for search/ranking/recommendation concepts — not just the skills field. Catches candidates who built real retrieval systems but never explicitly listed "FAISS" or "Pinecone".

Gated by technical title to prevent false positives (SEO content writers whose prose contains "ranked on page 1 of search results" don't get credit).

3. Title Gate (the most important fix)

A wrong-role candidate (HR Manager, Accountant, Frontend Developer) receives title_score = 0.05. Without a gate, they could still rank high if career/behavioral scores are strong.

The title gate (0.15 + 0.85 × title_score) is applied to the entire base score, not just an 18% slice — so a wrong-role candidate's total is suppressed to ~19% of what it would otherwise be.

4. Softened Availability Multiplier

# v1/v2: final = base × availability  → ghost candidate (avail=0.2) → 80% penalty
# v3:    final = base × (0.75 + 0.25 × availability)  → same ghost → 20% penalty

The JD says to "down-weight" inactive candidates, not eliminate them. A Senior ML Engineer inactive for 3 months is still a better hire than an active HR Manager.

5. Honeypot Detection

21 honeypots detected across 100,000 candidates:


Expert proficiency + 0 duration_months on 3+ skills (impossible)
5+ expert skills with 0 endorsements each (impossible on a real profile)
AI skill bolted onto frontend/devops stack with only 1 AI skill group showing depth


All honeypots scored 0.0001 — kept out of top 100.

6. Company Normalization

python"Google India" → "google"
"Google LLC"   → "google"
"Amazon Web Services" → "amazon"
"Meta Platforms" → "meta"

Prevents false negatives on real Tier-1 experience.


Output Format

csvcandidate_id,rank,score,reasoning
CAND_0081846,1,0.8643,"Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recruiter-facing search product at Razorpay (6.7 yrs as Lead AI Engineer). Open to work; 73% recruiter response rate; active recently; 30d notice; based in Bangalore."
CAND_0018499,2,0.8563,"Built a RAG-based ranking pipeline serving 50M+ queries per month for an internal recruiter-facing search product at Zomato (7.2 yrs as Senior ML Engineer). ..."
...

Top 100 candidates ranked by descending score. Each row includes a specific, quantified reasoning sentence extracted from the candidate's actual career description — not a template.


Results (on 100K candidate pool)

MetricValueTop-1 score0.8643Score range (top 100)0.8643 → 0.7126Avg title fit (top 100)1.000Avg skill depth (top 100)0.723Avg availability× (top 100)0.921Honeypots detected21Runtime (100K, CPU)~4 minutesValidation✅ Submission is valid

Top-1 candidate: Lead AI Engineer at Razorpay — built RAG-based ranking pipeline serving 50M+ queries/month, active, 30-day notice, strong recruiter response rate.


 # Project Structure

redrob-submission/
├── rank.py                  ← Main ranking engine (v3)
├── validate_submission.py   ← Official format validator
├── candidates.jsonl         ← 100K candidate pool (not in repo — too large)
├── my_team.csv              ← Submission output (top 100 ranked candidates)
└── README.md


What Doesn't Work (and Why We Didn't Do It)


LLM/API calls at ranking time — not allowed (no network during ranking per submission spec)
Vector embeddings — would require a model download, violating the pure-stdlib constraint
Neural learning-to-rank — no training labels available; would need recruiter feedback data


The pure rule-based + fuzzy semantic approach is appropriate given the constraints. For a production system, you'd add LLM re-ranking of the top-500 shortlist as a second pass.


Author

Aastha Singh
Submitted for the Redrob Data & AI Challenge — Intelligent Candidate Discovery Track
