# Assumptions

1. **Scope:** MoveInSync employee app only (`com.moveinsync.ets`), country India. Partner apps (Driver app, transport admin portals) and competitors are excluded.
2. **Reported Experiences vs. Root Causes:** Review text describes commuter-reported experiences and symptoms, not confirmed technical root causes. Suspected owner tags (`app_engineering`, `backend_routing`, `operations`, `client_policy`, `support_process`, `unclear`) are working hypotheses requiring internal engineering/telemetry validation.
3. **Public Review Selection Bias:** Public written reviews skew significantly negative (28% at 1-2 stars in the last 90 days) compared to the overall store rating (7.1% at 1-2 stars). Sample metrics describe vocal reviewers, not the silent majority.
4. **Store Rating vs. Rolling Window:** Store rating is cumulative and anchored across 114,881 ratings (headroom is small). Primary performance and lift impact are therefore evaluated against the **rolling 90-day window**.
5. **Misdirected Reviews:** Feedback from drivers, vendors, or admins reviewing their partner role rather than the employee rider journey is flagged as `misdirected_review` and excluded from rider friction themes.
6. **Languages:** English, Hindi (Devanagari script), and Hinglish (Romanized Hindi) reviews are classified directly without translation. Non-English volume is under 1% of the corpus.
7. **Data Access Boundary:** Analysis is strictly bounded to public Google Play Store data. Internal application crash logs, APM traces, customer support tickets, and in-app rating-prompt trigger logic were not accessible.
8. **Text Coverage:** Analysis covers written reviews only (~23,626 reviews), which represent a subset (~20%) of all store ratings.
9. **Classified Sample & Credit Constraints:** 
   - Eligible universe: 3,178 reviews (last 24 months, $\ge 3$ words).
   - Classified sample: 990 reviews (~31%) spanning February to October 2026, processed newest-first due to API credit limits.
   - The sample star distribution mirrors the eligible universe within 4.4 percentage points, and star-reweighted theme shares differ by under 1.0 percentage point.
10. **Version 12.19.0 Hypothesis:** An early skim hypothesized a performance regression on release 12.19.0. Statistical hypothesis testing yielded $z = 1.40$ ($p \approx 0.16$), confirming the dip is not statistically significant and falls within normal sample variance.
11. **Rating-Lift Simulation:**
    - Evaluated on the last 90 days ($N = 721$ reviews, 205 at 1-2 stars).
    - Conservative case: Affected low-star reviews improve to 3 stars.
    - Optimistic case: Affected reviews match the non-complaint average (~4.3 stars).
    - Assumes the 8-month classified theme distribution holds across the 90-day window.

---

### Analysis Windows & Filtering
- **Theme Analysis**: Recent classified cohort (~8 months, February–October 2026, $n = 434$ low-star reviews).
- **Headline Metrics**: Last 90 days.
- **Rating Trend**: Full store history (2014–2026).
- **Short Reviews**: Reviews under 3 words are flagged as `too_short`. They remain in rating calculations but are excluded from LLM theme assignment. Short 1-2 star reviews (*"worst app"*, *"bakwas"*) are tracked separately as `low_no_detail` (190 reviews) so theme shares are not artificially inflated.