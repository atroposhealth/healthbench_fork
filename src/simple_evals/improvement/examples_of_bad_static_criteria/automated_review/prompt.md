You are a medical expert. You will be presented with two pieces of information. 

1) A rubric criterion that was used to score an LLM response as part of a separate task, e.g. "Accurately presents the efficacy hierarchy of current medications, identifying tirzepatide (Zepbound) as having superior efficacy (approximately 21% weight loss) compared to other options, citing clinical trial data." 
2) A study result, e.g. "This cohort study compared weight loss outcomes between adult patients prescribed semaglutide (n=153729) and those prescribed tirzepatide (n=20815) between January 2022 and December 2024. After propensity score matching, patients on semaglutide experienced a significant average BMI change of -1.3 compared to tirzepatide, as well as a significant average weight loss of -3.6 kg compared to tirzepatide. Additionally, the semaglutide cohort had a significant average first BMI after 1 year of 0.47 compared to tirzepatide, and a significant average first weight after 1 year of 0.99 kg compared to tirzepatide."

Your job is to determine whether the study result contradicts the instructions in the criterion. For example, the study finding above does contradict the rubric criterion because the criterion states that tirzepatide is more effective than other weight-loss drugs while the study finds that semaglutide is more effective than tirzepatide.

Respond in the following JSON format:

{
    "explanation": <str>
    "study_contradicts_rubric": <bool>
}

---

Criterion:
{{criterion}}

Study Result:
{{study_result}}