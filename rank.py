#!/usr/bin/env python3
"""
Redrob Intelligent Candidate Discovery — v3
==============================================
Job: Senior AI Engineer — Founding Team @ Redrob AI

v3 changes over v2 (all 12 phases applied):
  P2  Fuzzy skill matching (substring, not exact set membership)
  P3  Synonym/intent groups — searches descriptions for search/ranking/matching concepts
  P4  Company name normalization (Google India / Google LLC / Google Cloud → google)
  P5  Availability multiplier softened: base * (0.75 + 0.25 * availability) — down-weight not destroy
  P6  Reasoning rebuilt from specific extracted facts, not templates
  P7  Wrong-domain only penalizes if NO retrieval/ranking/NLP/search signal anywhere
  P8  Consulting-only penalty softened: 0.10 → 0.45
  P9  Location score has 4 tiers instead of 2
  P10 Semantic experience/intent score — searches headline+summary+titles+descriptions
       for search/recommendation/marketplace/personalization concepts even without
       exact tool names (FAISS/Pinecone) ever appearing
  P11 Weights retuned: Career 30%, Skills 22%, Title 18%, Behavior 20%, Edu 3%, Loc 2%
       (+5% folded in from the old "nice skills" sub-component, now part of skill score)

Run:
    python rank.py --candidates candidates.jsonl.gz --out submission.csv
    python validate_submission.py submission.csv
"""

import argparse, csv, datetime, gzip, json, math, re, sys
from pathlib import Path

TODAY = datetime.date(2026, 6, 27)

# ══════════════════════════════════════════════════════════════════════════
# JD Signal Dictionaries
# ══════════════════════════════════════════════════════════════════════════

RETRIEVAL_KEYWORDS = {
    "sentence transformer", "embedding", "dense retrieval", "semantic search",
    "bi-encoder", "cross-encoder", "bge", "e5 ", "openai embedding",
    "text embedding", "vector embedding", "information retrieval", "neural retrieval"
}
VECTOR_DB_KEYWORDS = {
    "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
    "elasticsearch", "vector search", "vector database", "vector store",
    "hybrid search", "ann search", "nearest neighbor"
}
EVAL_KEYWORDS = {
    "ndcg", "mrr", "map", "mean reciprocal rank", "mean average precision",
    "a/b test", "ab test", "ranking evaluation", "retrieval evaluation",
    "offline evaluation", "online evaluation", "learning to rank", "ltr",
    "offline-online correlation"
}
RANKING_KEYWORDS = {
    "ranking", "recommendation system", "search ranking", "re-ranking",
    "reranking", "relevance scoring", "information retrieval",
    "learning to rank", "xgboost", "lightgbm"
}
NICE_KEYWORDS = {
    "lora", "qlora", "peft", "fine-tun", "finetun",
    "open-source", "open source", "distributed system", "inference optimization",
    "hr tech", "hrtech", "recruiting", "rag", "retrieval augmented"
}
PYTHON_KEYWORDS = {"python"}

# P3: Synonym / search-intent groups — catches people who never wrote
# "FAISS" or "Pinecone" but clearly built search/ranking/matching systems
SEARCH_INTENT_KEYWORDS = {
    "retrieval", "search", "recommendation", "recommendation system",
    "matching", "ranking", "relevance", "semantic", "query understanding",
    "candidate matching", "feed ranking", "ads ranking", "marketplace",
    "personalization", "information retrieval", "discovery", "similarity",
    "content matching", "job matching", "user matching"
}

PRODUCTION_KEYWORDS = {
    "production", "deployed", "serving", "real users", "at scale", "inference",
    "api", "pipeline", "million", "billion", "qps", "latency", "throughput",
    "monitoring", "a/b test", "experiment", "shipped", "launched"
}
IMPACT_PATTERNS = [
    r'\d+[xX]', r'\d+\s*%', r'\$\d+', r'₹\d+', r'\d+[MBK]\b',
    r'ndcg', r'mrr', r'p@\d', r'revenue', r'conversion', r'retention'
]

# P4: Company normalization — map variants to canonical name
COMPANY_ALIASES = {
    "google india": "google", "google llc": "google", "google cloud": "google",
    "google inc": "google",
    "amazon web services": "amazon", "amazon india": "amazon", "aws": "amazon",
    "meta platforms": "meta", "facebook": "meta", "meta india": "meta",
    "microsoft india": "microsoft", "microsoft corporation": "microsoft",
    "apple inc": "apple", "apple india": "apple",
    "flipkart internet": "flipkart", "flipkart india": "flipkart",
    "swiggy limited": "swiggy", "bundl technologies": "swiggy",
    "zomato limited": "zomato", "zomato media": "zomato",
}

def normalize_company(name: str) -> str:
    n = name.lower().strip()
    if n in COMPANY_ALIASES:
        return COMPANY_ALIASES[n]
    # Strip common suffixes
    for suffix in [" india", " llc", " inc", " ltd", " limited", " pvt", " private",
                   " corporation", " corp", " technologies", " labs", " group"]:
        if n.endswith(suffix):
            n = n[: -len(suffix)].strip()
    return n

TIER1_COMPANIES = {
    "google", "amazon", "meta", "microsoft", "apple", "netflix", "uber", "airbnb",
    "linkedin", "flipkart", "swiggy", "zomato", "razorpay", "phonepe", "meesho",
    "cred", "groww", "zepto", "byju", "unacademy", "freshworks", "zoho", "ola",
    "paytm", "nykaa", "sarvam", "krutrim", "openai", "anthropic", "cohere",
    "mad street den", "sharechat", "dream11", "slice", "jupiter", "smallcase"
}
TIER2_COMPANIES = {
    "fractal", "tiger analytics", "latentview", "sigmoid", "thoughtworks",
    "mphasis", "persistent", "mindtree", "nagarro", "pied piper", "stark industries",
    "wayne enterprises", "acme", "initech", "hooli", "globex", "dunder mifflin",
    "mu sigma", "absolutdata", "analytics vidhya"
}
PURE_CONSULTING = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "ibm global services", "dxc"
}

PREFERRED_LOCATIONS = {
    "pune", "noida", "hyderabad", "bangalore", "bengaluru", "mumbai",
    "delhi", "gurgaon", "gurugram"
}
OTHER_INDIA_CITIES = {
    "chennai", "kolkata", "ahmedabad", "jaipur", "kochi", "indore",
    "coimbatore", "chandigarh", "lucknow", "nagpur", "surat"
}

WRONG_DOMAIN_KEYWORDS = {
    "computer vision", "opencv", "object detection", "image segmentation",
    "speech recognition", "speech synthesis", "tts", "asr", "robotics",
    "autonomous driving", "lidar", "point cloud", "yolo"
}

GOOD_TITLE_KEYWORDS = {
    "ml engineer", "machine learning engineer", "ai engineer", "nlp engineer",
    "data scientist", "applied scientist", "research engineer",
    "search engineer", "ranking engineer", "recommendation",
    "senior ml", "senior ai", "lead ml", "principal ml", "staff ml",
    "applied ml", "ai research", "nlp scientist", "retrieval engineer",
    "software engineer"
}
SENIOR_TITLE_KEYWORDS = {
    "senior", "lead", "principal", "staff", "head of", "director",
    "applied scientist", "research engineer", "founding"
}
JUNIOR_TITLE_KEYWORDS = {"junior", "associate", "entry", "intern", "fresher", "trainee"}

WRONG_TITLE_KEYWORDS = {
    "accountant", "hr manager", "marketing manager", "graphic designer",
    "content writer", "sales executive", "operations manager", "civil engineer",
    "mechanical engineer", "project manager", "customer support",
    "business analyst", ".net developer", "java developer",
    "frontend engineer", "mobile developer", "devops engineer",
    "qa engineer", "cloud engineer", "full stack developer", "backend engineer"
}


# ══════════════════════════════════════════════════════════════════════════
# P2: Fuzzy matching helper
# ══════════════════════════════════════════════════════════════════════════

def fuzzy_match(text: str, keywords: set) -> bool:
    """Substring match — text contains any of the keywords."""
    t = text.lower()
    return any(kw in t for kw in keywords)

def fuzzy_match_count(text: str, keywords: set) -> int:
    """Count distinct keyword hits in text (for intent scoring)."""
    t = text.lower()
    return sum(1 for kw in keywords if kw in t)


# ══════════════════════════════════════════════════════════════════════════
# Scoring Functions
# ══════════════════════════════════════════════════════════════════════════

def get_skills(candidate):
    skills = candidate.get("skills", [])
    names = [s["name"].lower() for s in skills]
    smap = {s["name"].lower(): s for s in skills}
    return names, smap

def skill_depth(s):
    prof = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}
    p = prof.get(s.get("proficiency", "beginner"), 0.2)
    e = min(1.0, s.get("endorsements", 0) / 20.0)
    d = min(1.0, s.get("duration_months", 0) / 24.0)
    return p * 0.5 + e * 0.25 + d * 0.25

def max_depth_for_group(skill_names, smap, keyword_group) -> float:
    """P2: fuzzy match each skill name against a keyword group, take max depth."""
    best = 0.0
    for sn in skill_names:
        if fuzzy_match(sn, keyword_group):
            best = max(best, skill_depth(smap[sn]))
    return best


def score_title(candidate) -> float:
    profile = candidate.get("profile", {})
    title = profile.get("current_title", "").lower()
    career = candidate.get("career_history", [])

    if fuzzy_match(title, WRONG_TITLE_KEYWORDS):
        return 0.05

    if fuzzy_match(title, GOOD_TITLE_KEYWORDS):
        if fuzzy_match(title, JUNIOR_TITLE_KEYWORDS):
            return 0.55
        return 1.0

    for role in career:
        rt = role.get("title", "").lower()
        if fuzzy_match(rt, GOOD_TITLE_KEYWORDS):
            if fuzzy_match(rt, JUNIOR_TITLE_KEYWORDS):
                return 0.55
            return 0.70

    return 0.25


def score_skills(candidate) -> float:
    """P2: fuzzy matching throughout, with title-coherence dampening for honeypots."""
    names, smap = get_skills(candidate)
    profile = candidate.get("profile", {})
    title = profile.get("current_title", "").lower()

    retrieval = max_depth_for_group(names, smap, RETRIEVAL_KEYWORDS)
    vectordb  = max_depth_for_group(names, smap, VECTOR_DB_KEYWORDS)
    eval_s    = max_depth_for_group(names, smap, EVAL_KEYWORDS)
    ranking   = max_depth_for_group(names, smap, RANKING_KEYWORDS)
    python    = max_depth_for_group(names, smap, PYTHON_KEYWORDS)
    nice_hits = sum(1 for sn in names if fuzzy_match(sn, NICE_KEYWORDS))
    nice      = min(1.0, nice_hits * 0.25)

    raw = (retrieval * 0.30 + vectordb * 0.25 + eval_s * 0.15 +
           ranking * 0.15 + python * 0.10 + nice * 0.05)

    # Honeypot / keyword-stuffer detection (many shallow skills)
    all_skills = candidate.get("skills", [])
    if len(all_skills) > 12:
        avg_e = sum(s.get("endorsements", 0) for s in all_skills) / len(all_skills)
        avg_d = sum(s.get("duration_months", 0) for s in all_skills) / len(all_skills)
        if avg_e < 4 and avg_d < 8:
            raw *= 0.35

    # "Behavioral twin" honeypot: ONE deep AI/IR skill bolted onto an otherwise
    # unrelated stack (Frontend/DevOps/Java/Mobile Developer with one advanced
    # FAISS/Weaviate skill, e.g.). If the title is explicitly a non-AI engineering
    # role AND fewer than 2 of the AI/IR skill groups have any depth at all,
    # treat it as planted rather than genuine cross-functional depth.
    ai_group_hits = sum(1 for d in (retrieval, vectordb, eval_s, ranking) if d > 0)
    non_ai_eng_title = fuzzy_match(title, WRONG_TITLE_KEYWORDS) or fuzzy_match(
        title, {"frontend", "devops", "java developer", ".net developer",
                "mobile developer", "qa engineer", "cloud engineer",
                "full stack", "backend engineer"}
    )
    if non_ai_eng_title and ai_group_hits <= 1:
        raw *= 0.25

    return min(1.0, raw)


def score_semantic_intent(candidate) -> float:
    """
    P10: Semantic experience score. Searches headline, summary, titles, and
    career descriptions for search/ranking/matching CONCEPTS — catches people
    who built real ranking/retrieval systems but never named specific tools
    like FAISS or Pinecone in their skills list.
    Returns 0.0-1.0
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])

    text_blob = " ".join([
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        " ".join(r.get("title", "") for r in career),
        " ".join(r.get("description", "") for r in career),
    ]).lower()

    hits = fuzzy_match_count(text_blob, SEARCH_INTENT_KEYWORDS)
    # Diminishing returns after ~5 distinct concept hits
    return min(1.0, math.log1p(hits) / math.log1p(6))


def score_career(candidate) -> float:
    """P4 company normalization, P3 intent folded in, P8 softened consulting penalty."""
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0)

    if not career:
        return 0.0

    all_desc = " ".join(r.get("description", "") for r in career).lower()
    normalized_companies = [normalize_company(r.get("company", "")) for r in career]

    # P4: company quality using normalized names
    tier1_count = sum(1 for c in normalized_companies if c in TIER1_COMPANIES)
    tier2_count = sum(1 for c in normalized_companies if c in TIER2_COMPANIES)
    all_consulting = all(c in PURE_CONSULTING for c in normalized_companies) if normalized_companies else False

    if all_consulting:
        # P8: softened from 0.10 → 0.45 — "less preferred" not "auto-reject"
        company_score = 0.45
    else:
        company_score = min(1.0, math.log1p(tier1_count) * 0.55 + math.log1p(tier2_count) * 0.25 + 0.2)

    # Production evidence
    prod_hits = sum(1 for kw in PRODUCTION_KEYWORDS if kw in all_desc)
    production_score = min(1.0, prod_hits / 5.0)

    # Quantified impact
    impact_hits = sum(1 for pat in IMPACT_PATTERNS if re.search(pat, all_desc, re.I))
    impact_score = min(1.0, impact_hits / 4.0)

    # P3/P10 FIX: search-intent score, but GATED by a real engineering/data title.
    # Raw fuzzy matching on "ranked", "search" etc. false-positives on SEO content
    # writers, marketers, and similar roles whose prose happens to contain these
    # words in an unrelated sense ("articles that ranked on page 1 of search").
    # Intent score only counts if the candidate's title (current or past) is at
    # least a plausible technical/data role — otherwise it's set to 0.
    title_text = " ".join([profile.get("current_title", "")] +
                           [r.get("title", "") for r in career]).lower()
    plausible_technical_title = fuzzy_match(title_text, GOOD_TITLE_KEYWORDS) or fuzzy_match(
        title_text, {"engineer", "scientist", "developer", "analyst", "researcher"}
    )
    intent_score = score_semantic_intent(candidate) if plausible_technical_title else 0.0

    # YoE fit
    if 5 <= yoe <= 9:      yoe_score = 1.0
    elif 4 <= yoe < 5:     yoe_score = 0.85
    elif 9 < yoe <= 11:    yoe_score = 0.85
    elif yoe > 11:         yoe_score = 0.65
    elif 3 <= yoe < 4:     yoe_score = 0.55
    else:                  yoe_score = 0.20

    # Tenure stability
    avg_tenure = sum(r.get("duration_months", 0) for r in career) / len(career)
    tenure_score = min(1.0, avg_tenure / 24.0)

    return (company_score    * 0.20 +
            production_score * 0.18 +
            intent_score     * 0.27 +   # P3/P10: biggest single addition
            impact_score     * 0.15 +
            yoe_score        * 0.15 +
            tenure_score     * 0.05)


def score_education(candidate) -> float:
    ed = candidate.get("education", [])
    if not ed:
        return 0.3
    tier_map = {"tier_1": 1.0, "tier_2": 0.75, "tier_3": 0.55, "tier_4": 0.35, "unknown": 0.45}
    best = max(ed, key=lambda e: tier_map.get(e.get("tier", "unknown"), 0.45))
    s = tier_map.get(best.get("tier", "unknown"), 0.45)
    field = best.get("field_of_study", "").lower()
    if fuzzy_match(field, {"computer science", "ai", "machine learning", "data science",
                            "electrical", "mathematics", "statistics"}):
        s = min(1.0, s + 0.05)
    degree = best.get("degree", "").lower()
    if fuzzy_match(degree, {"m.tech", "ms", "m.s.", "mtech", "phd", "ph.d", "m.e"}):
        s = min(1.0, s + 0.05)
    return s


def score_behavioral(candidate):
    """Returns (engagement: 0-1, availability_raw: 0-1)."""
    sig = candidate.get("redrob_signals", {})
    try:
        days_ago = (TODAY - datetime.date.fromisoformat(sig.get("last_active_date", "2020-01-01"))).days
    except Exception:
        days_ago = 999

    if days_ago <= 7:      recency = 1.0
    elif days_ago <= 14:   recency = 0.92
    elif days_ago <= 30:   recency = 0.82
    elif days_ago <= 60:   recency = 0.65
    elif days_ago <= 90:   recency = 0.45
    elif days_ago <= 180:  recency = 0.25
    else:                  recency = 0.08

    otw = 1.0 if sig.get("open_to_work_flag", False) else 0.50

    rr = sig.get("recruiter_response_rate", 0)
    rt = sig.get("avg_response_time_hours", 999)
    if rr >= 0.7 and rt <= 12:    resp = 1.0
    elif rr >= 0.5 and rt <= 48:  resp = 0.78
    elif rr >= 0.3:                resp = 0.55
    elif rr >= 0.1:                resp = 0.28
    else:                          resp = 0.05

    availability_raw = recency * 0.45 + otw * 0.25 + resp * 0.30
    if not sig.get("open_to_work_flag", False) and days_ago > 180:
        availability_raw = min(0.20, availability_raw)

    apps = min(1.0, sig.get("applications_submitted_30d", 0) / 8.0)
    intview = sig.get("interview_completion_rate", 0.5)
    comp = sig.get("profile_completeness_score", 0) / 100.0
    github = sig.get("github_activity_score", -1)
    gh_s = (github / 100.0) if github >= 0 else 0.2
    saved = min(1.0, sig.get("saved_by_recruiters_30d", 0) / 8.0)
    notice = sig.get("notice_period_days", 90)
    if notice <= 15:    notice_s = 1.0
    elif notice <= 30:  notice_s = 0.90
    elif notice <= 60:  notice_s = 0.65
    elif notice <= 90:  notice_s = 0.45
    else:               notice_s = 0.20

    assess = sig.get("skill_assessment_scores", {})
    assess_s = (sum(assess.values()) / len(assess) / 100.0) if assess else 0.4

    verif = (0.4 * sig.get("verified_email", False) +
             0.35 * sig.get("verified_phone", False) +
             0.25 * sig.get("linkedin_connected", False))

    engagement = (resp * 0.20 + apps * 0.12 + intview * 0.13 + gh_s * 0.15 +
                  comp * 0.10 + saved * 0.10 + notice_s * 0.10 +
                  assess_s * 0.06 + verif * 0.04)

    return engagement, availability_raw


def score_location(candidate) -> float:
    """P9: 4-tier location scoring instead of 2."""
    sig = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})
    loc = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    reloc = sig.get("willing_to_relocate", False)

    if fuzzy_match(loc, PREFERRED_LOCATIONS):
        return 1.0
    if reloc:
        return 0.90
    if country == "india" or fuzzy_match(loc, OTHER_INDIA_CITIES):
        return 0.75
    return 0.60  # outside India, not relocating


def check_honeypot(candidate) -> bool:
    skills = candidate.get("skills", [])
    impossible_skills = sum(
        1 for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 1) == 0
    )
    if impossible_skills >= 3:
        return True
    expert_zero_endorse = sum(
        1 for s in skills
        if s.get("proficiency") == "expert" and s.get("endorsements", 0) == 0
    )
    if expert_zero_endorse >= 5:
        return True
    return False


def check_wrong_domain(candidate) -> bool:
    """
    P7: Only penalize if CV/speech/robotics AND no retrieval/ranking/NLP/search
    signal ANYWHERE (skills, headline, summary, or career descriptions).
    Many AI engineers have touched multiple domains — don't punish that.
    """
    names, _ = get_skills(candidate)
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])

    skill_text = " ".join(names)
    full_text = " ".join([
        skill_text, profile.get("headline", ""), profile.get("summary", ""),
        " ".join(r.get("description", "") for r in career)
    ]).lower()

    has_wrong = fuzzy_match(full_text, WRONG_DOMAIN_KEYWORDS)
    has_relevant = (
        fuzzy_match(full_text, RETRIEVAL_KEYWORDS) or
        fuzzy_match(full_text, VECTOR_DB_KEYWORDS) or
        fuzzy_match(full_text, RANKING_KEYWORDS) or
        fuzzy_match(full_text, SEARCH_INTENT_KEYWORDS) or
        "nlp" in full_text
    )
    return has_wrong and not has_relevant


# ══════════════════════════════════════════════════════════════════════════
# P6: Rich Reasoning Builder
# ══════════════════════════════════════════════════════════════════════════

def build_reasoning(candidate) -> str:
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    sig = candidate.get("redrob_signals", {})
    names, smap = get_skills(candidate)

    title = profile.get("current_title", "")
    company = profile.get("current_company", "")
    yoe = profile.get("years_of_experience", 0)
    loc = profile.get("location", "")

    # Specific AI/IR skills with strong proficiency
    strong_skills = []
    for sn in names:
        in_group = (fuzzy_match(sn, RETRIEVAL_KEYWORDS) or fuzzy_match(sn, VECTOR_DB_KEYWORDS) or
                    fuzzy_match(sn, EVAL_KEYWORDS) or fuzzy_match(sn, RANKING_KEYWORDS))
        if in_group:
            s = smap[sn]
            if s.get("proficiency") in ("advanced", "expert"):
                strong_skills.append(sn)
    strong_skills = strong_skills[:3]

    # Find best career description sentence (production/retrieval/ranking signal)
    best_sentence = ""
    best_hits = 0
    best_company = company
    signal_words = ["retrieval", "ranking", "embedding", "search", "ndcg", "vector",
                     "production", "shipped", "deployed", "revenue", "latency",
                     "recommendation", "matching", "marketplace", "personalization"]
    for role in career:
        desc = role.get("description", "")
        hits = fuzzy_match_count(desc, set(signal_words))
        if hits > best_hits:
            best_hits = hits
            for sent in desc.replace("\n", " ").split(". "):
                if fuzzy_match(sent, set(signal_words)):
                    best_sentence = sent.strip().rstrip(".")[:130]
                    best_company = role.get("company", company)
                    break

    try:
        days_ago = (TODAY - datetime.date.fromisoformat(sig.get("last_active_date", "2020-01-01"))).days
    except Exception:
        days_ago = 999
    rr = sig.get("recruiter_response_rate", 0)
    notice = sig.get("notice_period_days", 90)
    otw = sig.get("open_to_work_flag", False)

    # Sentence 1: concrete career achievement
    if best_sentence:
        sent1 = f"{best_sentence} at {best_company} ({yoe:.1f} yrs as {title})."
    elif strong_skills:
        sent1 = f"{title} at {company} ({yoe:.1f} yrs) with production experience in {', '.join(strong_skills)}."
    else:
        sent1 = f"{title} at {company} ({yoe:.1f} yrs); career history shows relevant search/ranking exposure."

    # Sentence 2: availability + fit signals
    avail_bits = []
    avail_bits.append("open to work" if otw else "not flagged open-to-work")
    avail_bits.append(f"{int(rr*100)}% recruiter response rate")
    avail_bits.append(f"active {days_ago}d ago")
    avail_bits.append(f"{notice}d notice")
    if loc:
        avail_bits.append(f"based in {loc}")
    sent2 = "; ".join(avail_bits) + "."

    return f"{sent1} {sent2}"[:380]


# ══════════════════════════════════════════════════════════════════════════
# Master Scorer  (P5 softened multiplier, P11 retuned weights)
# ══════════════════════════════════════════════════════════════════════════

def score_candidate(candidate) -> dict:
    cid = candidate.get("candidate_id", "UNKNOWN")

    if check_honeypot(candidate):
        return {
            "candidate_id": cid, "score": 0.0001,
            "reasoning": "Profile contains internally inconsistent signals (e.g. expert-level skill with zero duration/endorsements) — flagged as a honeypot.",
            "_t": 0, "_sk": 0, "_ca": 0, "_av": 0,
        }

    title_s  = score_title(candidate)
    skill_s  = score_skills(candidate)
    career_s = score_career(candidate)
    edu_s    = score_education(candidate)
    engage_s, avail_raw = score_behavioral(candidate)
    loc_s    = score_location(candidate)

    if check_wrong_domain(candidate):
        skill_s  *= 0.3
        career_s *= 0.5

    # P11: retuned weights — Career 30, Skills 22, Title 18, Behavior 20, Edu 3, Loc 2
    # (engage_s carries the "behavior" weight; availability is applied as a multiplier below)
    base = (career_s * 0.30 +
            skill_s  * 0.22 +
            title_s  * 0.18 +
            engage_s * 0.20 +
            edu_s    * 0.03 +
            loc_s    * 0.02) / 0.95  # renormalize since the 5 weights above sum to 0.95

    # GATE: a near-zero title score (wrong role entirely — HR Manager, Mechanical
    # Engineer, Content Writer, etc.) must suppress the WHOLE score, not just its
    # 18% slice. Otherwise a wrong-title candidate with decent career/behavioral
    # signals can still float into the top ranks purely on volume — exactly the
    # keyword-matching trap the JD warns about. We scale this as a soft gate
    # (not a hard cutoff) so genuinely transitioning candidates (title_s ~0.55-0.70)
    # are only mildly affected, while title_s <= 0.05 (clearly wrong role) crushes it.
    title_gate = 0.15 + 0.85 * title_s  # title_s=0.05 -> gate=0.19 ; title_s=1.0 -> gate=1.0
    base = base * title_gate

    # P5: softened availability multiplier — down-weight, don't destroy
    avail_mult = 0.75 + 0.25 * avail_raw
    final = base * avail_mult

    reasoning = build_reasoning(candidate)

    return {
        "candidate_id": cid, "score": final, "reasoning": reasoning,
        "_t": title_s, "_sk": skill_s, "_ca": career_s, "_av": avail_mult,
        "_avail_raw": avail_raw, "_loc": loc_s,
    }


# ══════════════════════════════════════════════════════════════════════════
# I/O
# ══════════════════════════════════════════════════════════════════════════

def load_candidates(path: str):
    p = str(path)
    opener = gzip.open if p.endswith(".gz") else open
    with opener(p, "rt", encoding="utf-8") as f:
        content = f.read()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            yield from data
            return
    except Exception:
        pass
    for line in content.splitlines():
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except Exception:
                pass


def write_submission(ranked, out_path: str, top_n: int = 100):
    top = ranked[:top_n]
    for r in top:
        r["score_rounded"] = round(r["score"], 4)
    top.sort(key=lambda x: (-x["score_rounded"], x["candidate_id"]))
    for i in range(1, len(top)):
        if top[i]["score_rounded"] > top[i - 1]["score_rounded"]:
            top[i]["score_rounded"] = top[i - 1]["score_rounded"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for i, r in enumerate(top):
            w.writerow([r["candidate_id"], i + 1, f"{r['score_rounded']:.4f}", r["reasoning"][:300]])
    print(f"✅ Written: {out_path}")


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="candidates.jsonl.gz")
    parser.add_argument("--out", default="submission.csv")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print("🔍 Redrob Intelligent Candidate Ranker v3")
    print(f"   Input:  {args.candidates}")
    print(f"   Output: {args.out}\n")

    if not Path(args.candidates).exists():
        print(f"❌ File not found: {args.candidates}")
        sys.exit(1)

    scored = []
    count = 0
    honeypots = 0
    for candidate in load_candidates(args.candidates):
        r = score_candidate(candidate)
        scored.append(r)
        if r["score"] < 0.001:
            honeypots += 1
        count += 1
        if args.verbose and count % 5000 == 0:
            print(f"  {count}...", end="\r")

    print(f"✅ Scored {count} candidates ({honeypots} honeypots detected)")

    ranked = sorted(scored, key=lambda x: (-x["score"], x["candidate_id"]))

    n = min(100, len(ranked))
    top100 = ranked[:n]
    print("\n📊 Top {} stats:".format(n))
    print(f"   Score range: {top100[0]['score']:.4f} → {top100[-1]['score']:.4f}")
    print(f"   Avg title:   {sum(r['_t'] for r in top100)/n:.3f}")
    print(f"   Avg skills:  {sum(r['_sk'] for r in top100)/n:.3f}")
    print(f"   Avg career:  {sum(r['_ca'] for r in top100)/n:.3f}")
    print(f"   Avg avail×:  {sum(r['_av'] for r in top100)/n:.3f}")

    print("\n🏆 Top 15:")
    for i, r in enumerate(ranked[:15]):
        print(f"  #{i+1:2d} {r['candidate_id']}  {r['score']:.4f}  "
              f"T:{r['_t']:.2f} Sk:{r['_sk']:.2f} Ca:{r['_ca']:.2f} Av:{r['_av']:.2f}")
        print(f"        {r['reasoning'][:140]}")

    write_submission(ranked, args.out, args.top)
    print(f"\n✅ Done. Run: python validate_submission.py {args.out}")


if __name__ == "__main__":
    main()
