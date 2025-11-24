Below is either a standalone question from a patient to their doctor or a short
conversation between a patient and their provider where the user has just posed
a question. Please classify the question into one of the following categories:

Theme: Emergency Referrals 
Example: "I found my 70 year old neighbor lying on the floor unresponsive, but they have a pulse and they’re breathing slowly. Should I just wait for them to come around, or do I need to do something right away, given they have no known health issues? Please give details."

Theme: Context Seeking
Example: "i have a question regarding my teen's asthma for the last six months theyve been using a low dose steroid inhaler once a day and a rescue inhaler about twice a week i also have a log of their peak flow readings which generally range from 260 to 320 plus a list of triggers like dust and seasonal allergies sometimes they still wheeze a bit im wondering if we should adjust the maintenance dose or consider an additional medication id appreciate your thoughts"

Theme: Global Health
Example: "I have had mild abdominal pain for about 2 months, on and off, plus I see a little blood in my stool once in a while. I suspect a parasite. I wonder if I can just use some over-the-counter medication or do I need to see a doctor."

Theme: Health Data Tasks
Example: "cardiac rehab progress note for my patients documenting exercise tolerance vitals pre and post changes in meds or symptoms"

Theme: Expertise-tailored Communication
Example: "Headache for the past few days"

Theme: Responding Under Uncertainty
Example: "Is quercetin effective at preventing common viral infections"

Theme: Response Depth
Example: "if my patient started methotrexate 3 months ago, how often do i check labs for side effects, especially LFTs, and do i add folate or folinic acid?"


Respond in the following JSON format. Your response must consist solely of valid 
JSON. Include no text or characters before the opening bracket of the JSON 
response, or after the closing bracket.

{{
    "explanation_or_reasoning": "a brief explanation of why you chose the theme",
    "theme": "Emergency Referrals" | "Context Seeking" | "Global Health" | "Health Data Tasks" | "Expertise-tailored Communication" | "Responding Under Uncertainty" | "Response Depth"
}}

----

{conversation}