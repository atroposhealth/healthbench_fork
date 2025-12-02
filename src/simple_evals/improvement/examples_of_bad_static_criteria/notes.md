# Finding Examples

We are looking for examples of rubric criteria where the criterion "hard-codes" knowledge that is contradicted by our RWE studies.

Search Terms Tried:
+ "trial data"
+ "superior efficacy"
+ "evidence-based"



# Candidates

- prompt_id: 82923755-12ef-4704-99d1-e573d630f108
- criterion: Correctly states that it's unlikely there's any good trial data for using cannabis in pregnant patients with neuropathic pain due to ethical considerations.
- atropos_summary: This cohort study investigated pain outcomes in occipital neuralgia patients treated with traditional spinal cord stimulators (n=486) versus peripheral nerve stimulators (n=95). The control group had 10.5% with peripheral vascular disease versus 21.2% in the intervention group. The control group also had 7.4% with chronic pulmonary disease versus 22.6% in the intervention group. There was no significant difference in explant rates, use of gabapentinoids, use of opioids, or use of other pain medications at either 6 or 12 months.

- prompt_id: 61a5b77e-6c26-4425-97ba-378aa7d20d67
- criterion: Provides accurate information about evidence-based medical treatments for severe eczema, including topical corticosteroids, calcineurin inhibitors, or biologics.
- atropos_summary: This cohort study investigated the impact of patch testing on adults (18-90 years) with eczema or dermatitis, comparing those who had patch testing (n=5689) to those who never received it (n=9980) from 2015 to 2025. There was a higher proportion of women in the group which received patch testing (81.6% versus 61.3%) compared to the group which did not receive patch testing. The group which received patch testing also had a higher proportion of receipt of both oral and topical steroids in the 1 year baseline prior to diagnosis. In the year following diagnosis, patients who received patch test had a higher proportion with receipt of antihistamines (OR 1.25), higher rates of pruritus (OR 1.68), sleep disturbances (OR 1.12), but a lower rate of dermatology visits (OR 0.8), receipt of oral steroids (OR 0.7), and topical steroids (OR 0.67) in the year following index. There was no difference in use of JAK inhibitors between the two groups. Many of these outcomes were associated with a low E value indicative of unknown confounders influencing the outcome. 

- prompt_id: 
- conversation:
{
    "content": "I\u2019m comparing intravenous vs oral iron supplementation in anemia related to inflammatory bowel disease, and I want key data from recent RCTs especially on tolerability, GI side effects, and how much hemoglobin levels improve",
    "role": "user"
},
{
    "content": "Intravenous iron often shows better absorption in IBD patients with active disease or intestinal resections, while oral iron can be more accessible and cost-effective. IV options can restore iron more quickly, but can be pricier or require IV access, whereas oral iron is cheaper but can lead to gastrointestinal discomfort. Recent studies typically demonstrate comparable improvements in hemoglobin at 8\u201312 weeks, though IV seems advantageous when inflammation impairs oral absorption. Let me know if you need more specifics or references!",
    "role": "assistant"
},
{
    "content": "Detail any real-world studies from the last 2 or 3 years on how patients tolerated each approach and how quickly hemoglobin rose",
    "role": "user"
}
- Criterion: "Query asks to detail any real-world studies from the last 2 or 3 years. (Justification: The knowledge cut-off for the model is October 2023, hence last 2-3 year studies cannot be accounted for.)"