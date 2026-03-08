"""
OnboardAI — Business Data Preparation
Loads or generates business knowledge base and test Q&A pairs.

For real businesses: replace the sample data with your own.
For demo: generates a realistic sample coffee shop business.

Usage:
    python prepare.py                     # Generate sample data
    python prepare.py --stats             # Show data statistics
    python prepare.py --import docs/      # Import .txt/.md files as knowledge
"""

import json
import os
import argparse
import glob
from datetime import datetime
from typing import List, Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge.json")
TEST_FILE = os.path.join(DATA_DIR, "test_qa.json")
SEED = 42

# ═══ Sample Business: "BeanWave Coffee" ═════════════════════════════════════
# Replace this with your own business data for real use.

SAMPLE_KNOWLEDGE = [
    {
        "topic": "Company Overview",
        "content": (
            "BeanWave Coffee is a specialty coffee roaster and café chain founded "
            "in 2019 in Austin, Texas. We operate 12 locations across Texas and "
            "Oklahoma. Our mission is 'exceptional coffee, zero waste.' We source "
            "beans directly from farms in Ethiopia, Colombia, and Guatemala through "
            "our Direct Trade program, paying farmers 40% above fair-trade minimums."
        ),
    },
    {
        "topic": "Menu & Products",
        "content": (
            "Core drinks: Espresso ($3.50), Americano ($4), Latte ($5), Cappuccino "
            "($4.75), Cold Brew ($5), Nitro Cold Brew ($6), Matcha Latte ($5.50). "
            "Seasonal: Pumpkin Spice Latte (fall), Lavender Honey Latte (spring), "
            "Mango Cold Brew (summer). Food: avocado toast ($8), banana bread ($4), "
            "açaí bowl ($9), breakfast burrito ($7). All milk alternatives (oat, "
            "almond, coconut) are free of charge. We offer 3 roast levels: Light "
            "(Sunrise), Medium (Midday), Dark (Midnight)."
        ),
    },
    {
        "topic": "Loyalty Program",
        "content": (
            "BeanWave Rewards: earn 1 point per $1 spent. 50 points = free drink. "
            "100 points = free food item. Birthday reward: free drink + pastry. "
            "Gold tier (500+ points/year): 1.5x points, early access to seasonal "
            "drinks, free size upgrades. Platinum tier (1000+ points/year): 2x "
            "points, free monthly bag of beans, exclusive tasting events. Points "
            "expire after 12 months of inactivity. Register via our app or website."
        ),
    },
    {
        "topic": "Ordering & Delivery",
        "content": (
            "Order in-store, via our BeanWave app (iOS/Android), or through our "
            "website. Delivery available through DoorDash and UberEats within a "
            "5-mile radius of each location. Delivery fee: $2.99, waived for "
            "orders over $20. App orders get 10% off and skip the line. "
            "Catering available for events: minimum order $100, requires 48-hour "
            "advance notice. Custom corporate packages available."
        ),
    },
    {
        "topic": "Hours & Locations",
        "content": (
            "Standard hours: Mon-Fri 6am-8pm, Sat-Sun 7am-9pm. Downtown Austin "
            "flagship: 6am-10pm daily. Drive-through available at 5 locations "
            "(Round Rock, Cedar Park, Plano, Frisco, Norman). Holiday hours vary "
            "— check the app. All locations have free WiFi, power outlets, and "
            "meeting rooms bookable through the app (free for first hour, $10/hr "
            "after)."
        ),
    },
    {
        "topic": "Sustainability",
        "content": (
            "Zero-waste commitment: all cups are compostable, we offer $0.50 "
            "discount for bringing your own cup. Coffee grounds are composted and "
            "donated to community gardens. We carbon-offset all shipping. Our "
            "roasting facility runs on 100% renewable energy. Packaging is 100% "
            "recyclable. We publish an annual sustainability report on our website."
        ),
    },
    {
        "topic": "Jobs & Careers",
        "content": (
            "We hire baristas ($16-$20/hr + tips), shift leads ($22/hr), and store "
            "managers ($55-65k salary). Benefits include health insurance (full-time), "
            "free coffee during shifts, 1 free bag of beans per week, 401k matching "
            "up to 4%, and a $1500/year education stipend. Apply on our careers page "
            "or email jobs@beanwave.coffee. We promote from within — 80% of our "
            "managers started as baristas."
        ),
    },
    {
        "topic": "Returns & Complaints",
        "content": (
            "Wrong drink? We'll remake it immediately, no questions asked. "
            "Unsatisfied with beans purchased online? Full refund within 30 days, "
            "keep the beans. Equipment refunds within 14 days with receipt. For "
            "complaints, email support@beanwave.coffee or call (512) 555-BEAN. "
            "Response time: within 4 hours during business hours. We log all "
            "feedback and review trends weekly with store managers."
        ),
    },
    {
        "topic": "Wholesale & B2B",
        "content": (
            "We supply beans to 50+ restaurants and offices in Texas. Wholesale "
            "pricing: 20-40% off retail depending on volume. Minimum order: 10 lbs. "
            "Free delivery for orders over 50 lbs within Austin metro. We provide "
            "free brewing equipment loans for accounts ordering 100+ lbs/month. "
            "Contact wholesale@beanwave.coffee or call (512) 555-BULK."
        ),
    },
    {
        "topic": "Gift Cards & Merchandise",
        "content": (
            "Gift cards available in $10, $25, $50, and custom amounts. Purchase "
            "in-store, on our website, or in the app. Gift cards never expire. "
            "Merchandise: branded mugs ($15), tumblers ($25), t-shirts ($20), "
            "tote bags ($12), and brewing kits ($45). Corporate bulk orders get "
            "15% off for 20+ items."
        ),
    },
]

# Test Q&A pairs — these are what the AI model must answer correctly.
# Include both factual and conversational styles.

SAMPLE_TEST_QA = [
    {
        "question": "What are your hours?",
        "expected_answer": "Mon-Fri 6am-8pm, Sat-Sun 7am-9pm. Downtown Austin flagship is open 6am-10pm daily.",
        "category": "hours",
        "difficulty": "easy",
    },
    {
        "question": "How much is a latte?",
        "expected_answer": "A latte is $5. Milk alternatives (oat, almond, coconut) are free.",
        "category": "menu",
        "difficulty": "easy",
    },
    {
        "question": "Do you have oat milk? Is there an extra charge?",
        "expected_answer": "Yes, we offer oat milk, almond milk, and coconut milk. All milk alternatives are free of charge.",
        "category": "menu",
        "difficulty": "easy",
    },
    {
        "question": "How does your rewards program work?",
        "expected_answer": "Earn 1 point per $1 spent. 50 points gets you a free drink, 100 points a free food item. You also get a free drink and pastry on your birthday.",
        "category": "loyalty",
        "difficulty": "medium",
    },
    {
        "question": "I ordered a cappuccino but got a latte. What can you do?",
        "expected_answer": "We'll remake your drink immediately, no questions asked. Just let the barista know or bring it back to the counter.",
        "category": "complaints",
        "difficulty": "medium",
    },
    {
        "question": "Can I book a meeting room?",
        "expected_answer": "Yes, meeting rooms are bookable through the BeanWave app. The first hour is free, then $10/hour after that.",
        "category": "locations",
        "difficulty": "medium",
    },
    {
        "question": "What's your sustainability policy?",
        "expected_answer": "We have a zero-waste commitment: compostable cups, $0.50 discount for your own cup, composted coffee grounds, carbon-offset shipping, 100% renewable energy roasting, and recyclable packaging.",
        "category": "sustainability",
        "difficulty": "medium",
    },
    {
        "question": "Are you hiring? What's the pay for baristas?",
        "expected_answer": "Yes! Baristas earn $16-$20/hr plus tips, with benefits including health insurance, free coffee, 401k matching, and a $1500/year education stipend. Apply at our careers page or email jobs@beanwave.coffee.",
        "category": "careers",
        "difficulty": "medium",
    },
    {
        "question": "I want to serve your coffee at my restaurant. How does wholesale work?",
        "expected_answer": "Wholesale pricing is 20-40% off retail depending on volume. Minimum order is 10 lbs, free delivery for 50+ lbs in Austin metro. We also provide free brewing equipment for accounts ordering 100+ lbs/month. Contact wholesale@beanwave.coffee.",
        "category": "wholesale",
        "difficulty": "hard",
    },
    {
        "question": "What's the cheapest drink you have?",
        "expected_answer": "An espresso at $3.50 is our most affordable drink.",
        "category": "menu",
        "difficulty": "easy",
    },
    {
        "question": "I bought beans online and don't like the taste. Can I get a refund?",
        "expected_answer": "Yes, full refund within 30 days, and you can keep the beans. Email support@beanwave.coffee or call (512) 555-BEAN.",
        "category": "complaints",
        "difficulty": "medium",
    },
    {
        "question": "How do I reach Gold tier in your rewards program?",
        "expected_answer": "Earn 500+ points in a year to reach Gold tier. You'll get 1.5x points, early access to seasonal drinks, and free size upgrades.",
        "category": "loyalty",
        "difficulty": "hard",
    },
    {
        "question": "What's your company's story?",
        "expected_answer": "BeanWave Coffee was founded in 2019 in Austin, Texas. We're a specialty roaster with 12 locations across Texas and Oklahoma. Our mission is 'exceptional coffee, zero waste,' and we source beans directly from farms through our Direct Trade program, paying 40% above fair-trade minimums.",
        "category": "company",
        "difficulty": "medium",
    },
    {
        "question": "Do you deliver? How much does it cost?",
        "expected_answer": "Yes, we deliver through DoorDash and UberEats within 5 miles of each location. Delivery fee is $2.99, waived for orders over $20. You can also order through our app for 10% off.",
        "category": "ordering",
        "difficulty": "medium",
    },
    {
        "question": "I need coffee for a company event of 50 people. Can you help?",
        "expected_answer": "Absolutely! We offer catering with a minimum order of $100 and 48-hour advance notice. For corporate needs, we also have custom corporate packages. Order through our app or contact us directly.",
        "category": "ordering",
        "difficulty": "hard",
    },
    {
        "question": "Do gift cards expire?",
        "expected_answer": "No, BeanWave gift cards never expire. They're available in $10, $25, $50, or custom amounts.",
        "category": "gift_cards",
        "difficulty": "easy",
    },
    {
        "question": "My friend's birthday is coming up. What's a good gift under $50?",
        "expected_answer": "Great options under $50 include a gift card ($25 or $50), a branded tumbler ($25), a brewing kit ($45), or a mug ($15) paired with a bag of beans.",
        "category": "gift_cards",
        "difficulty": "hard",
    },
    {
        "question": "What seasonal drinks do you have right now?",
        "expected_answer": "Our seasonal drinks rotate: Pumpkin Spice Latte in fall, Lavender Honey Latte in spring, and Mango Cold Brew in summer. Check our app or ask in-store for the current seasonal menu.",
        "category": "menu",
        "difficulty": "medium",
    },
    {
        "question": "Where are your drive-through locations?",
        "expected_answer": "We have drive-through at 5 locations: Round Rock, Cedar Park, Plano, Frisco, and Norman.",
        "category": "locations",
        "difficulty": "medium",
    },
    {
        "question": "I left my laptop charger at your downtown store yesterday. How do I get it back?",
        "expected_answer": "Please contact the Downtown Austin flagship location or email support@beanwave.coffee with a description. Our team keeps lost items for 30 days. You can also call us at (512) 555-BEAN.",
        "category": "complaints",
        "difficulty": "hard",
    },
]


# ═══ Functions ═══════════════════════════════════════════════════════════════

def generate_sample_data() -> dict:
    """Generate the sample BeanWave Coffee business data."""
    return {
        "business_name": "BeanWave Coffee",
        "industry": "Food & Beverage / Coffee",
        "knowledge_base": SAMPLE_KNOWLEDGE,
        "generated_at": datetime.now().isoformat(),
    }


def generate_test_qa() -> dict:
    """Generate test Q&A pairs."""
    return {
        "business_name": "BeanWave Coffee",
        "test_pairs": SAMPLE_TEST_QA,
        "total_questions": len(SAMPLE_TEST_QA),
        "categories": list(set(q["category"] for q in SAMPLE_TEST_QA)),
        "generated_at": datetime.now().isoformat(),
    }


def import_documents(docs_dir: str) -> List[Dict]:
    """Import .txt and .md files from a directory as knowledge base entries."""
    entries = []
    for ext in ("*.txt", "*.md"):
        for filepath in glob.glob(os.path.join(docs_dir, "**", ext), recursive=True):
            with open(filepath, "r", errors="ignore") as f:
                content = f.read().strip()
            if content:
                topic = os.path.splitext(os.path.basename(filepath))[0]
                topic = topic.replace("-", " ").replace("_", " ").title()
                entries.append({"topic": topic, "content": content[:5000]})
                print(f"  📄 Imported: {filepath} → '{topic}' ({len(content)} chars)")
    return entries


def print_stats(knowledge: dict, test_qa: dict):
    """Print data statistics."""
    kb = knowledge.get("knowledge_base", [])
    qa = test_qa.get("test_pairs", [])
    total_chars = sum(len(e["content"]) for e in kb)

    print(f"\n{'═' * 55}")
    print(f"  OnboardAI — Data Statistics")
    print(f"  Business: {knowledge.get('business_name', '?')}")
    print(f"{'═' * 55}")
    print(f"  Knowledge base:     {len(kb)} topics, {total_chars:,} chars")
    print(f"  Test questions:     {len(qa)}")
    print(f"  Categories:         {', '.join(test_qa.get('categories', []))}")
    print()

    # Difficulty breakdown
    by_diff = {}
    for q in qa:
        d = q.get("difficulty", "unknown")
        by_diff[d] = by_diff.get(d, 0) + 1
    for d, count in sorted(by_diff.items()):
        print(f"    {d:10s}  {count} questions")

    print(f"\n{'═' * 55}\n")


# ═══ Main ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OnboardAI — Data Preparation")
    parser.add_argument("--stats", action="store_true", help="Show data statistics")
    parser.add_argument("--import-docs", type=str, metavar="DIR",
                        help="Import .txt/.md files from directory")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    if args.import_docs:
        print(f"Importing documents from {args.import_docs}...")
        entries = import_documents(args.import_docs)
        if entries:
            # Merge with existing or create new
            if os.path.exists(KNOWLEDGE_FILE):
                with open(KNOWLEDGE_FILE) as f:
                    knowledge = json.load(f)
                knowledge["knowledge_base"].extend(entries)
            else:
                knowledge = {
                    "business_name": "Your Business",
                    "industry": "Your Industry",
                    "knowledge_base": entries,
                    "generated_at": datetime.now().isoformat(),
                }
            with open(KNOWLEDGE_FILE, "w") as f:
                json.dump(knowledge, f, indent=2)
            print(f"  ✅ Imported {len(entries)} topics into {KNOWLEDGE_FILE}")
        else:
            print("  ⚠️  No documents found.")
    elif args.stats:
        if os.path.exists(KNOWLEDGE_FILE) and os.path.exists(TEST_FILE):
            with open(KNOWLEDGE_FILE) as f:
                knowledge = json.load(f)
            with open(TEST_FILE) as f:
                test_qa = json.load(f)
            print_stats(knowledge, test_qa)
        else:
            print("Run `python prepare.py` first to generate data.")
    else:
        print("Generating sample business data (BeanWave Coffee)...")
        knowledge = generate_sample_data()
        with open(KNOWLEDGE_FILE, "w") as f:
            json.dump(knowledge, f, indent=2)
        print(f"  ✅ Knowledge base: {KNOWLEDGE_FILE}")

        test_qa = generate_test_qa()
        with open(TEST_FILE, "w") as f:
            json.dump(test_qa, f, indent=2)
        print(f"  ✅ Test Q&A: {TEST_FILE}")

        print_stats(knowledge, test_qa)
        print("  💡 Replace the sample data with your own business data,")
        print("     or use --import-docs to load .txt/.md files.\n")
