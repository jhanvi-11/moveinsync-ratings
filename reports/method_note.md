# MoveInSync Play Store Ratings: Technical Method Note

**Date**: 13 October 2026  
**Scope**: MoveInSync employee app (`com.moveinsync.ets`)  
**Companion Documents**: [Recommendation Memo](memo.md), [Assumptions](assumptions.md), [Scope](scope.md)  

---

## 1. Data Ingestion & Storage

### Source & Acquisition
- **Target Application**: Google Play Store package `com.moveinsync.ets`, country `in` (India).
- **Tooling**: Ingested via `google-play-scraper` on 12 October 2026.
- **Historical Scope**: 24,318 written reviews collected spanning 2014 through 11 October 2026.
- **Storage & Deduplication**: Stored locally in SQLite (`data/reviews.db`) using an `INSERT ... ON CONFLICT(review_id) DO UPDATE` pattern on `review_id`. A second incremental scraping execution yielded 0 duplicate rows, verifying complete capture.
- **Privacy & PII**: Reviewer usernames and avatar URLs were stripped during ingestion.
- **Store Benchmark Reconciliation**:
  - Store headline: **4.639** from **114,881 ratings** (with ~23,626 written reviews).
  - Star histogram: 7,315 (1★), 839 (2★), 1,224 (3★), 7,253 (4★), 98,244 (5★).
  - Mathematically calculated weighted average: **4.6389**, perfectly reconciling with the displayed store score.

### Analytical Windows
1. **Headline Performance**: Rolling **last 90 days** (capturing current operational reality).
2. **Taxonomy & Complaint Themes**: Recent cohort of classified reviews spanning **9 February to 11 October 2026** (~8 months).
3. **Historical Trajectory**: Complete historical dataset (2014–2026) for multi-year trend analysis.

---

## 2. Preprocessing & Data Cleaning

- **Eligible Classification Universe**: Reviews from the last 24 months containing at least 3 words and genuine textual content (3,178 reviews).
- **Short Review Handling (`too_short`)**:
  - Reviews under 3 words constitute ~45% of recent reviews and are overwhelmingly positive (e.g., *"good"*, *"nice app"*).
  - **190 one- and two-star short reviews** (e.g., *"worst app"*, *"bad"*) were tagged as `low_no_detail` and tracked separately to prevent artificial inflation of specific functional themes.
- **Language Identification**:
  - Non-English reviews accounted for under 1% of recent volume (18 of 5,803 reviews).
  - Script detection identified Devanagari Hindi; a specialized token vocabulary tagged Romanized Hindi (Hinglish). Non-English reviews were classified directly without translation.

---

## 3. LLM Classification & Taxonomy Engine

### Taxonomy Design (v1)
A standardized 19-label mutually exclusive primary taxonomy:
`login_otp`, `booking_failure`, `cab_late_no_show`, `wrong_route_eta`, `live_tracking_gps`, `boarding_verification`, `crash_lag`, `notifications`, `driver_behavior`, `safety`, `support_unresponsive`, `billing_payment`, `ui_confusion`, `rating_prompt`, `update_issue`, `feature_request`, `praise`, `misdirected_review`, `other`.

### Model Execution & Schema Enforcement
- **Model**: LLM accessed via OpenRouter API (`anthropic/claude-5.5-haiku`), temperature `0`, batch size `15`.
- **Structured Output**: Strictly enforced using Pydantic schema validation:
  - `primary_theme`, `secondary_themes`
  - `journey_stage` (9 stages)
  - `sentiment` (`neg`, `neu`, `pos`)
  - `severity` (integer scale 1 to 5)
  - `suspected_owner` (`app_engineering`, `backend_routing`, `operations`, `client_policy`, `support_process`, `unclear`)
  - `evidence_quote` (exact substring up to 20 words)
  - `confidence` (float 0.0 to 1.0)
- **Credit Limit & Sample Representativeness**:
  - Due to API credit constraints, **990 of 3,178 eligible reviews (31.2%)** were classified.
  - Because classification ran from newest to oldest, the sample captures the most recent operational period (Feb–Oct 2026).
  - The classified star distribution closely matched the full eligible set (5-star was 45.8% in sample vs. 41.4% in full set). Raw and star-reweighted theme shares differ by under 1.0 percentage point.

---

## 4. Ground Truth Validation & Agreement

### Sampling & Benchmarking
- 80 reviews were stratified across star ratings (oversampling 1-2 star complaints where friction resides).
- **27 gold reviews** fell within the classified cohort (`data/gold_overlap.csv`).
- Gold labels were drafted with AI assistance and independently audited row-by-row; 5 of 27 labels were manually refined.

### Inter-Annotator Agreement Metrics (n = 27)
- **Primary Theme Agreement**: **89.0%** | **Cohen’s Kappa ($\kappa$): 0.87** (Near-perfect agreement).
- **Suspected Owner Agreement**: **81.0%** | **Cohen’s Kappa ($\kappa$): 0.67** (Substantial agreement).
- **Binary Complaint vs. Non-Complaint**: **100.0%** agreement.
- **Error Analysis**: The 3 theme discrepancies occurred on multi-issue reviews (e.g., login complaint combined with routing feedback) or boundary cases between `feature_request` and `booking_failure`. The model exhibited a slight tendency to prioritize `login_otp` when multiple complaints co-occurred.
- **Low Confidence Rate**: 10.4% of classifications had model confidence < 0.50 (predominantly vague text).

---

## 5. Statistical & Analytical Methods

### 1. Theme Share & Reweighting
For 1-2 star classified reviews ($n = 434$):
$$\text{Weight } w_s = \frac{P_{\text{eligible}}(\text{Star} = s)}{P_{\text{classified}}(\text{Star} = s)}$$
Both raw proportions and reweighted proportions were computed.

### 2. Rating-Lift Simulation
Conducted on the full last-90-day review cohort ($N = 721$ reviews, $N_{\text{low}} = 205$ at 1-2 stars, baseline average $3.81$):
- Estimated reviews affected for theme $i$: $k_i = \text{Weighted Share}_i \times N_{\text{low}}$.
- **Conservative Lift**: Affected reviews improve to 3 stars:
  $$\Delta_{\text{cons}} = \frac{k_i \cdot (3.0 - \bar{x}_{\text{low}})}{N}$$
- **Optimistic Lift**: Affected reviews improve to the non-complaint average ($\bar{x}_{\text{non-low}} \approx 4.3$):
  $$\Delta_{\text{opt}} = \frac{k_i \cdot (\bar{x}_{\text{non-low}} - \bar{x}_{\text{low}})}{N}$$

### 3. Release Version Hypothesis Testing
Tested whether release `12.19.0` represented a statistically significant regression in negative reviews against the preceding five releases (`12.18.0`, `12.18.1`, `12.17.0`, `12.16.1`, `12.16.0`):
- Pooled two-proportion test yielded **$z = 1.40$ ($p \approx 0.16$)**.
- Concluded: Not statistically significant at $\alpha = 0.05$. Small-sample variance is typical across minor app updates.

### 4. Emerging Themes (Rate of Change)
Compared 1-2 star complaint shares in the last 30 days ($n = 60$) against the prior 90 days ($n = 202$):
- Highlighted `crash_lag` increasing from 15.8% to 31.7% ($\Delta = +15.9\%$).
- Treated as a prioritized operational signal rather than definitive proof, given monthly sample size.

---

## 6. Tools & Methodological Reproducibility

- **Stack**: Python 3.13, `google-play-scraper`, `pandas`, `sqlite3`, `pydantic`, `OpenRouter API`.
- **Reproducibility Pipeline**:
  - [`src/baseline.py`](../src/baseline.py): Captures daily store metadata.
  - [`src/scrape.py`](../src/scrape.py): Pulls incremental reviews.
  - [`src/clean.py`](../src/clean.py): Cleans and tags languages.
  - [`src/classify.py`](../src/classify.py): Classifies via taxonomy.
  - [`src/agreement.py`](../src/agreement.py): Computes Kappa vs. gold labels.
  - [`src/analyze.py`](../src/analyze.py): Exports lift models and theme shares to `data/out/`.

---

## 7. Limitations & Caveats

1. **Reviewer Selection Bias**: While 85.5% of store ratings are 5-star, 28% of written reviews are 1-2 star. Findings reflect friction among vocal reviewers.
2. **Sample Coverage**: Due to API credits, 31% of eligible reviews were classified. While sufficient for high statistical confidence, shares represent point estimates.
3. **Subjective Ownership**: Suspected owners reflect user perceptions. Technical bugs may stem from corporate IT proxies or telecom carriers rather than MoveInSync code.
4. **Vague Residual Bucket**: 17.7% of complaints fall into `other` / unclassifiable text, meaning named functional shares are conservative lower bounds.
5. **No Telemetry Access**: Public review scraping provides no visibility into client session logs, crash stack traces, or in-app rating prompt logic.
6. **2019 Volume Anomaly**: A historical spike of 6,051 reviews in 2019 remains unexplained and was excluded from recent baseline modeling.
