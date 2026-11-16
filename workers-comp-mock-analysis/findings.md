# New York State Workers' Compensation Claims Analysis

## Recommendations for Product and Strategy

### Hypothesis 1: Triage based on Predictive Severity and Pre-Existing Conditions

- **Observation:** Median claimant age and the prevalence of subjective soft-tissue injuries (strains or tears) are relevant trends to monitor. The analysis also considers changes in disallowance rates and their possible implications.
- **Product hypothesis:** Build an early causality scoring engine at initial intake (Form C-2/FROI) that uses claimant age, injury mechanics, and body part to estimate the likelihood of compensability disputes.
- **Client strategy value:** Route potentially complex claims to specialized nurse case managers or consider targeted early IME evaluations, rather than relying on blanket legal disputes or delayed investigation.

### Hypothesis 2: Section 32 Settlement Timing Predictor

- **Observation:** Changes in long-term statutory cash benefits (PPD/PTD), disallowances, and other claim dispositions may be influenced by statutory duration caps and Section 32 settlements.
- **Product hypothesis:** Build a settlement propensity and runout estimation tool to help benchmark when a controverted or indeterminate claim may be economically suitable for a Section 32 lump-sum waiver agreement.
- **Client strategy value:** Reduce indemnity reserve volatility and carrier defense expenses by surfacing potential closed-claim settlement opportunities before legal hearing backlogs accumulate.

## Next Steps

### Domain Research

Validate the analysis assumptions and product hypotheses with workers' compensation domain experts.

### Technical Perfection

Improve regex mapping for text fields, including cases where multiple mentions of the same body part appear.

## Findings

### Observations

#### Workers' Compensation Claims Across Zip Codes

The analysis considers patient-level measures (industry and wage), case-level measures (representation), and outcomes (controversion and days to hearing). Age and hearing count are also compared across zip codes.

#### Injury Patterns

OIICS describes injury from a medical perspective, while WCIO descriptions can combine the medical outcome with its workplace cause (for example, strain or injury by lifting).

- The three most frequently injured body parts reported in the analysis are lower back, knee, and fingers.
- About 72% of injuries are labeled traumatic in the OIICS classification.

### Trends

#### Demographics

- The analysis reports a rise in claims from healthcare workers.
- It reports a decrease in median age and an increase in soft-tissue claims.

#### Utilization

- Claim counts are generally higher, with volume smoothing out from peak years such as 2014 and 2019.

#### Outcomes

- Controversion rates decreased from 2000 to 2009 and have generally been steady since 2010.
- Disallowed or cancelled claims have proportionally increased, while claims receiving benefits have decreased.
- Medical-only outcomes have remained in a historically low range over the last 10 years.

### Litigation Implications

The supplied analysis examines claim identifier 111 and proposes estimating how the likelihood of reaching a judge might differ under represented versus unrepresented status, compared with the average association observed in the data.

A proposed statistical model treats `Highest Process` as a binary outcome and `Attorney/Representative` as a predictor. This is an association-based analysis, not a causal estimate of what would happen if an individual claim's representation status changed.

### Factors Associated with Reaching a Judge

The code compares judicial escalation with IME status and reporting lag. These comparisons are descriptive and should not be interpreted as causal effects without additional study design and controls.
