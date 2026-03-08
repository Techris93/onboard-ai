"""
OnboardAI — AI Configuration
The ONLY file the AI agent modifies.

Contains the system prompt, few-shot examples, response rules, and
retrieval settings that control how the AI answers business questions.
The agent iterates on these to maximize accuracy and quality.
"""

# ═══ System Prompt ═══════════════════════════════════════════════════════════
# This is the main instruction given to the AI before each question.
# The agent should refine this to improve answer quality.

SYSTEM_PROMPT = """You are a helpful customer service assistant for {business_name}.

Use the following knowledge base to answer customer questions accurately.
If the answer isn't in the knowledge base, say you'll connect them with a team member.

KNOWLEDGE BASE:
{knowledge_context}

---

Answer the customer's question based ONLY on the information above.
Be friendly, concise, and helpful."""


# ═══ Few-Shot Examples ═══════════════════════════════════════════════════════
# Teach the AI the expected response style by example.
# The agent can add, remove, or modify these.

FEW_SHOT_EXAMPLES = [
    {
        "question": "What time do you open?",
        "answer": "We're open Mon-Fri 6am-8pm and Sat-Sun 7am-9pm. Our Downtown Austin flagship stays open until 10pm daily!",
    },
    {
        "question": "How much is a coffee?",
        "answer": "Our espresso starts at $3.50, and a latte is $5. All milk alternatives (oat, almond, coconut) are free of charge!",
    },
]


# ═══ Response Rules ══════════════════════════════════════════════════════════
# Guidelines the AI should follow when crafting responses.

RESPONSE_RULES = [
    "Keep answers under 3 sentences when possible",
    "Include specific numbers (prices, hours, points) when available",
    "End with a helpful follow-up or invitation when appropriate",
    "Use a warm, friendly tone — not corporate or robotic",
]


# ═══ Retrieval Settings ══════════════════════════════════════════════════════
# Control how knowledge base documents are selected for context.

# How many knowledge topics to include in context (more = more info but slower)
MAX_CONTEXT_TOPICS = 5

# Minimum keyword overlap to consider a topic relevant (0.0 - 1.0)
RELEVANCE_THRESHOLD = 0.1

# Whether to include all knowledge or just relevant topics
USE_FULL_KNOWLEDGE = False


# ═══ Model Settings ══════════════════════════════════════════════════════════
# The agent can tune these for better quality.

TEMPERATURE = 0.3       # Lower = more factual, higher = more creative
MAX_TOKENS = 300        # Maximum response length


# ═══ Retrieval Logic ═════════════════════════════════════════════════════════

def _keyword_overlap(text1: str, text2: str) -> float:
    """Simple keyword overlap score between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    # Remove common stop words
    stop = {"the", "a", "an", "is", "are", "do", "does", "what", "how",
            "can", "i", "you", "your", "my", "in", "on", "at", "to",
            "for", "of", "and", "or", "it", "this", "that", "with"}
    words1 -= stop
    words2 -= stop
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / max(len(words1), len(words2))


def retrieve_context(question: str, knowledge_base: list) -> str:
    """Select relevant knowledge topics for a given question."""
    if USE_FULL_KNOWLEDGE:
        return "\n\n".join(
            f"**{entry['topic']}**: {entry['content']}"
            for entry in knowledge_base
        )

    # Score each topic by relevance
    scored = []
    for entry in knowledge_base:
        score = _keyword_overlap(question, entry["content"])
        topic_score = _keyword_overlap(question, entry["topic"])
        combined = max(score, topic_score * 1.5)  # topic match weighted higher
        scored.append((combined, entry))

    scored.sort(key=lambda x: -x[0])

    # Take top N topics above threshold
    relevant = [
        entry for score, entry in scored[:MAX_CONTEXT_TOPICS]
        if score >= RELEVANCE_THRESHOLD
    ]

    # Always include at least 1 topic even if none match well
    if not relevant and scored:
        relevant = [scored[0][1]]

    return "\n\n".join(
        f"**{entry['topic']}**: {entry['content']}"
        for entry in relevant
    )


def build_prompt(question: str, knowledge_base: list, business_name: str) -> str:
    """Build the full prompt to send to the AI model."""
    context = retrieve_context(question, knowledge_base)

    system = SYSTEM_PROMPT.format(
        business_name=business_name,
        knowledge_context=context,
    )

    # Add few-shot examples
    examples_text = ""
    if FEW_SHOT_EXAMPLES:
        examples_text = "\n\nHere are examples of how to respond:\n"
        for ex in FEW_SHOT_EXAMPLES:
            examples_text += f"\nCustomer: {ex['question']}\nAssistant: {ex['answer']}\n"

    # Add response rules
    rules_text = ""
    if RESPONSE_RULES:
        rules_text = "\n\nResponse guidelines:\n"
        for rule in RESPONSE_RULES:
            rules_text += f"- {rule}\n"

    full_prompt = system + examples_text + rules_text
    full_prompt += f"\n\nCustomer: {question}\nAssistant:"

    return full_prompt
