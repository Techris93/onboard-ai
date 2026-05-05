# OnboardAI — Agent Program

You are an autonomous prompt engineer. Your goal is to **maximize the combined score** (0-100) by optimizing the AI configuration in `config.py` so it accurately answers business-specific questions.

## Structure

```
prepare.py   — Loads business data & test Q&A (DO NOT MODIFY)
config.py    — AI configuration (YOU MODIFY THIS)
evaluate.py  — Scores AI responses against expected answers (DO NOT MODIFY)
data/        — Business knowledge base and test pairs
```

## Scoring (100 points)

| Component | Max | What It Measures |
|-----------|-----|-----------------|
| Accuracy | 50 | Do answers contain the right facts? |
| Quality | 30 | Are answers well-structured and appropriate length? |
| Coverage | 20 | What % of questions get a passing score? |

## Experiment Loop

```bash
python prepare.py              # Generate/load business data (once)
python evaluate.py --verbose   # Get baseline score with details
# Edit config.py
python evaluate.py             # Check if score improved
python evaluate.py --commit    # Auto-commit if improved
```

## What to Change in config.py

### System Prompt (`SYSTEM_PROMPT`)
- Make it more specific to the business
- Add instructions for handling edge cases
- Include tone/personality guidance
- Tell the AI how to handle unknown questions

### Few-Shot Examples (`FEW_SHOT_EXAMPLES`)
- Add examples for categories with low scores
- Match the desired response style and length
- Include examples of tricky questions

### Response Rules (`RESPONSE_RULES`)
- Add rules based on common failures
- E.g., "Always include prices when discussing menu items"
- E.g., "When asked about complaints, show empathy first"

### Retrieval Settings
- `MAX_CONTEXT_TOPICS` — More topics = more context but could dilute relevance
- `RELEVANCE_THRESHOLD` — Lower = more topics included, higher = fewer but more relevant
- `USE_FULL_KNOWLEDGE` — Set True for small knowledge bases
- Improve `retrieve_context()` logic for smarter topic selection

### Model Settings
- `TEMPERATURE` — Lower (0.1) for factual answers, higher (0.7) for creative ones
- `MAX_TOKENS` — Increase if answers are being cut off

## Strategies

1. **Check per-category scores** — Focus on the weakest categories first
2. **Add targeted few-shots** — One example per weak category helps a lot
3. **Improve retrieval** — If the right knowledge isn't reaching the model, accuracy drops
4. **Tune prompt structure** — Order matters: knowledge → examples → rules → question
5. **Test with `--verbose`** — See exactly what the AI says vs. what's expected

## For Your Own Business

Replace the sample data:

```bash
# Option A: Import documents
python prepare.py --import-docs path/to/your/docs/

# Option B: Edit data files directly
# Edit data/knowledge.json — your business knowledge
# Edit data/test_qa.json   — your test Q&A pairs
```

Then run the optimization loop until the AI knows your business.

## Adaptive Onboarding Path Signals

When the website workflow is used, the onboarding layer also tracks path quality:

- Mark a path **successful** when the route helped a user complete onboarding.
- Mark a path **stuck** when the user stalled, asked repeated clarification questions, or lost confidence.
- Use the Adaptive Path Signals panel to review confusion risk, path confidence, micro-questions, next best action, and adaptive training tone.

These signals do not replace `evaluate.py`; they guide the human onboarding route around the optimized assistant with confusion detection, path confidence, knowledge routing, team alignment, friction simulation, progressive access, timing optimization, priority routing, micro-checks, and tone adaptation.
