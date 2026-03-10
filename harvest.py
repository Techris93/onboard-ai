"""
OnboardAI — Business Data Harvester
Collect REAL business data for AI onboarding.

Three collection methods:
  1. Website scraping  — Crawl public pages for about, products, FAQ, policies
  2. Document parsing   — Extract text from PDFs, DOCX, CSV, TXT, MD
  3. Guided interview   — Interactive questionnaire for the business owner

Plus: AI-generated Q&A test pairs from the collected knowledge.

Usage:
    python harvest.py --url https://example.com        # Scrape website
    python harvest.py --url https://example.com --depth 2  # Crawl deeper
    python harvest.py --docs path/to/files/             # Parse documents
    python harvest.py --interview                       # Guided questionnaire
    python harvest.py --generate-qa                     # AI-generate test Q&A
    python harvest.py --status                          # Show collected data stats
"""

import json
import os
import re
import sys
import csv
import glob
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge.json")
TEST_FILE = os.path.join(DATA_DIR, "test_qa.json")
HARVEST_LOG = os.path.join(DATA_DIR, "harvest_log.json")


# ═══ Website Scraper ═════════════════════════════════════════════════════════

def scrape_website(url: str, max_pages: int = 15, depth: int = 1) -> List[Dict]:
    """Crawl a business website and extract structured knowledge."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("  ❌ Install dependencies: pip install requests beautifulsoup4")
        sys.exit(1)

    base_domain = urlparse(url).netloc
    visited = set()
    to_visit = [(url, 0)]
    entries = []

    # Page-type keywords for classification
    PAGE_TYPES = {
        "about": ["about", "our-story", "who-we-are", "mission", "team", "history"],
        "products": ["menu", "products", "services", "offerings", "shop", "catalog",
                      "pricing", "prices", "plans"],
        "contact": ["contact", "reach-us", "get-in-touch", "locations", "find-us",
                     "hours", "directions"],
        "faq": ["faq", "frequently-asked", "help", "support", "questions", "answers"],
        "policy": ["policy", "privacy", "terms", "refund", "return", "shipping",
                    "warranty", "guarantee", "cancellation"],
        "careers": ["careers", "jobs", "hiring", "work-with-us", "join-us",
                     "employment", "openings"],
        "blog": ["blog", "news", "updates", "articles", "press"],
    }

    headers = {
        "User-Agent": "OnboardAI-DataHarvester/1.0 (business-onboarding-tool)"
    }

    print(f"\n  🌐 Crawling {url} (max {max_pages} pages, depth {depth})...\n")

    while to_visit and len(visited) < max_pages:
        current_url, current_depth = to_visit.pop(0)

        # Normalize URL
        current_url = current_url.rstrip("/")
        if current_url in visited:
            continue

        # Skip non-HTML resources
        skip_ext = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".pdf", ".css",
                     ".js", ".zip", ".mp4", ".mp3", ".ico", ".woff", ".woff2")
        if any(current_url.lower().endswith(ext) for ext in skip_ext):
            continue

        visited.add(current_url)

        try:
            resp = requests.get(current_url, headers=headers, timeout=10,
                                allow_redirects=True)
            if resp.status_code != 200:
                continue
            if "text/html" not in resp.headers.get("Content-Type", ""):
                continue
        except requests.exceptions.SSLError:
            # Fallback for systems with broken SSL certs (e.g. macOS)
            try:
                resp = requests.get(current_url, headers=headers, timeout=10,
                                    allow_redirects=True, verify=False)
                if resp.status_code != 200:
                    continue
                if "text/html" not in resp.headers.get("Content-Type", ""):
                    continue
            except Exception as e:
                print(f"  ⚠️  Failed: {current_url} ({e})")
                continue
        except Exception as e:
            print(f"  ⚠️  Failed: {current_url} ({e})")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, nav, footer noise
        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()

        # Get page title
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Classify page type
        url_lower = current_url.lower()
        page_type = "general"
        for ptype, keywords in PAGE_TYPES.items():
            if any(kw in url_lower for kw in keywords):
                page_type = ptype
                break

        # Extract main content (try common content selectors)
        main_content = None
        for selector in ["main", "article", '[role="main"]',
                         ".content", "#content", ".main-content",
                         ".page-content", ".entry-content"]:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.body if soup.body else soup

        # Extract text, preserving structure
        text = _extract_structured_text(main_content)

        if len(text.strip()) < 50:
            continue

        # Detect topic from title or URL
        topic = _infer_topic(title, current_url, page_type)

        entry = {
            "topic": topic,
            "content": text[:5000],  # cap per entry
            "source_url": current_url,
            "page_type": page_type,
            "harvested_at": datetime.now().isoformat(),
        }
        entries.append(entry)
        print(f"  ✅ [{page_type:10s}] {topic[:50]:50s} ({len(text):,} chars)")

        # Find links on this page for deeper crawling
        if current_depth < depth:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)

                # Stay on the same domain
                if parsed.netloc != base_domain:
                    continue
                # Skip anchors and query-heavy URLs
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                if clean_url not in visited:
                    to_visit.append((clean_url, current_depth + 1))

    print(f"\n  📊 Scraped {len(entries)} pages from {len(visited)} visited URLs")
    return entries


def _extract_structured_text(element) -> str:
    """Extract text from HTML while preserving headers and lists."""
    lines = []
    for child in element.descendants:
        if child.name in ("h1", "h2", "h3", "h4"):
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n{text}")
        elif child.name == "li":
            text = child.get_text(strip=True)
            if text:
                lines.append(f"• {text}")
        elif child.name == "p":
            text = child.get_text(strip=True)
            if text:
                lines.append(text)
        elif child.name in ("td", "th"):
            text = child.get_text(strip=True)
            if text and len(text) > 2:
                lines.append(text)

    # Deduplicate consecutive identical lines
    filtered = []
    for line in lines:
        if not filtered or line != filtered[-1]:
            filtered.append(line)

    return "\n".join(filtered)


def _infer_topic(title: str, url: str, page_type: str) -> str:
    """Infer a clean topic name from the page title and URL."""
    if title:
        # Remove common suffixes like "| Company Name" or "- Company Name"
        clean = re.split(r'\s*[|\-–—]\s*', title)[0].strip()
        if len(clean) > 3:
            return clean

    # Fallback to URL path
    path = urlparse(url).path.strip("/")
    if path:
        last_segment = path.split("/")[-1]
        return last_segment.replace("-", " ").replace("_", " ").title()

    return page_type.replace("_", " ").title()


# ═══ Document Parser ═════════════════════════════════════════════════════════

def parse_documents(docs_path: str) -> List[Dict]:
    """Parse business documents from a directory."""
    entries = []

    if os.path.isfile(docs_path):
        files = [docs_path]
    else:
        files = []
        for ext in ("*.txt", "*.md", "*.pdf", "*.docx", "*.csv", "*.tsv"):
            files.extend(glob.glob(os.path.join(docs_path, "**", ext), recursive=True))

    if not files:
        print(f"  ⚠️  No supported files found in {docs_path}")
        return entries

    print(f"\n  📁 Parsing {len(files)} files from {docs_path}...\n")

    for filepath in sorted(files):
        ext = os.path.splitext(filepath)[1].lower()
        topic = os.path.splitext(os.path.basename(filepath))[0]
        topic = topic.replace("-", " ").replace("_", " ").title()

        try:
            if ext in (".txt", ".md"):
                content = _parse_text(filepath)
            elif ext == ".pdf":
                content = _parse_pdf(filepath)
            elif ext == ".docx":
                content = _parse_docx(filepath)
            elif ext in (".csv", ".tsv"):
                content = _parse_csv(filepath, delimiter="\t" if ext == ".tsv" else ",")
            else:
                continue

            if content and len(content.strip()) > 20:
                entries.append({
                    "topic": topic,
                    "content": content[:5000],
                    "source_file": filepath,
                    "harvested_at": datetime.now().isoformat(),
                })
                print(f"  ✅ {ext:5s}  {topic:40s} ({len(content):,} chars)")
            else:
                print(f"  ⚠️  {ext:5s}  {topic:40s} (too short, skipped)")

        except Exception as e:
            print(f"  ❌ {ext:5s}  {topic:40s} (error: {e})")

    print(f"\n  📊 Parsed {len(entries)} documents")
    return entries


def _parse_text(filepath: str) -> str:
    with open(filepath, "r", errors="ignore") as f:
        return f.read().strip()


def _parse_pdf(filepath: str) -> str:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("  ❌ Install PyPDF2: pip install PyPDF2")
        return ""

    reader = PdfReader(filepath)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _parse_docx(filepath: str) -> str:
    try:
        from docx import Document
    except ImportError:
        print("  ❌ Install python-docx: pip install python-docx")
        return ""

    doc = Document(filepath)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _parse_csv(filepath: str, delimiter: str = ",") -> str:
    """Convert CSV rows into readable text."""
    lines = []
    with open(filepath, "r", errors="ignore") as f:
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, None)
        if headers:
            for row in reader:
                if len(row) >= len(headers):
                    items = [f"{h}: {v}" for h, v in zip(headers, row) if v.strip()]
                    if items:
                        lines.append("; ".join(items))
    return "\n".join(lines[:200])  # cap rows


# ═══ Guided Interview ════════════════════════════════════════════════════════

INTERVIEW_QUESTIONS = [
    {
        "section": "Company Overview",
        "questions": [
            "What is the name of your business?",
            "What does your business do? (Describe in 2-3 sentences)",
            "When was it founded and where is it located?",
            "What is your mission or unique value proposition?",
        ],
    },
    {
        "section": "Products & Services",
        "questions": [
            "List your main products or services with prices:",
            "Do you have any seasonal or special offerings?",
            "What sets your products/services apart from competitors?",
        ],
    },
    {
        "section": "Hours & Locations",
        "questions": [
            "What are your business hours?",
            "List all your locations (address or area):",
            "Do you offer delivery or online services? Details:",
        ],
    },
    {
        "section": "Customer Policies",
        "questions": [
            "What is your return/refund policy?",
            "What is your cancellation policy?",
            "Any warranties or guarantees you offer?",
        ],
    },
    {
        "section": "Common Customer Questions",
        "questions": [
            "What are the TOP 5 questions customers ask most often? (List them with answers)",
            "What is the biggest complaint or pain point customers have?",
            "What information do customers often struggle to find?",
        ],
    },
    {
        "section": "Contact & Support",
        "questions": [
            "How can customers reach you? (phone, email, chat, social media)",
            "What is your typical response time?",
            "Is there a loyalty program, membership, or rewards system? Details:",
        ],
    },
]


def run_interview() -> List[Dict]:
    """Interactive questionnaire for business owners."""
    entries = []

    print(f"\n{'═' * 60}")
    print(f"  🎙️  OnboardAI — Business Interview")
    print(f"  Answer each question. Press Enter twice to skip.")
    print(f"  Type 'done' to finish early.")
    print(f"{'═' * 60}\n")

    for section in INTERVIEW_QUESTIONS:
        print(f"\n  ── {section['section']} ──\n")
        section_content = []

        for question in section["questions"]:
            print(f"  {question}")
            lines = []
            while True:
                try:
                    line = input("  > ")
                except (EOFError, KeyboardInterrupt):
                    print("\n  Interview ended.")
                    if section_content:
                        entries.append({
                            "topic": section["section"],
                            "content": "\n".join(section_content),
                            "source": "interview",
                            "harvested_at": datetime.now().isoformat(),
                        })
                    return entries

                if line.lower() == "done":
                    if section_content:
                        entries.append({
                            "topic": section["section"],
                            "content": "\n".join(section_content),
                            "source": "interview",
                            "harvested_at": datetime.now().isoformat(),
                        })
                    return entries
                if line == "":
                    break
                lines.append(line)

            if lines:
                answer = " ".join(lines)
                section_content.append(f"{question} {answer}")

        if section_content:
            entries.append({
                "topic": section["section"],
                "content": "\n".join(section_content),
                "source": "interview",
                "harvested_at": datetime.now().isoformat(),
            })
            print(f"  ✅ {section['section']} recorded")

    return entries


# ═══ AI Q&A Generator ════════════════════════════════════════════════════════

def generate_qa_pairs(knowledge: List[Dict], num_questions: int = 20) -> List[Dict]:
    """Use Gemini to generate realistic test Q&A from real knowledge."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("  ⚠️  GEMINI_API_KEY not set. Using rule-based Q&A generation.")
        return _generate_qa_rule_based(knowledge, num_questions)

    # Try to use Gemini
    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        # Build knowledge context
        context = "\n\n".join(
            f"## {entry['topic']}\n{entry['content']}"
            for entry in knowledge
        )

        prompt = f"""You are a Q&A dataset generator. Given the following business knowledge base, generate {num_questions} realistic customer questions with accurate answers.

RULES:
- Questions should be things REAL customers would ask (natural language, varied phrasing)
- Answers must be factually grounded in the knowledge base ONLY
- Include easy questions (hours, prices) and hard ones (policy edge cases, comparisons)
- Each answer should be 1-3 sentences, conversational and helpful
- Include specific details (prices, hours, names) when available

KNOWLEDGE BASE:
{context[:8000]}

Return ONLY valid JSON — an array of objects, each with:
- "question": the customer question
- "expected_answer": the correct answer
- "category": topic category (e.g., "menu", "hours", "policy")
- "difficulty": "easy", "medium", or "hard"

Return ONLY the JSON array, no markdown fences or other text."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # Parse response
        text = response.text.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

        qa_pairs = json.loads(text)

        if isinstance(qa_pairs, list) and len(qa_pairs) > 0:
            print(f"  🤖 AI generated {len(qa_pairs)} Q&A pairs")
            return qa_pairs

    except Exception as e:
        print(f"  ⚠️  Gemini Q&A generation failed: {e}")
        print(f"  Falling back to rule-based generation...")

    return _generate_qa_rule_based(knowledge, num_questions)


def _generate_qa_rule_based(knowledge: List[Dict], num_questions: int) -> List[Dict]:
    """Fallback: generate Q&A from knowledge using pattern matching."""
    pairs = []

    for entry in knowledge:
        topic = entry["topic"]
        content = entry["content"]

        # Extract prices
        prices = re.findall(r'([\w\s]+?)\s*[\(:]?\s*\$(\d+(?:\.\d{2})?)', content)
        for item, price in prices[:2]:
            pairs.append({
                "question": f"How much is {item.strip().lower()}?",
                "expected_answer": f"{item.strip()} is ${price}.",
                "category": topic.lower().replace(" ", "_"),
                "difficulty": "easy",
            })

        # Extract hours
        hours = re.findall(
            r'((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[\w-]*\s+\d+(?::\d+)?(?:am|pm)[\s-]+\d+(?::\d+)?(?:am|pm))',
            content, re.IGNORECASE
        )
        if hours:
            pairs.append({
                "question": f"What are your hours?",
                "expected_answer": "; ".join(hours[:3]),
                "category": "hours",
                "difficulty": "easy",
            })

        # Extract contact info
        emails = re.findall(r'[\w.+-]+@[\w.-]+', content)
        phones = re.findall(r'(?:\(\d{3}\)\s*)?[\d-]{7,}', content)
        if emails or phones:
            answer_parts = []
            if emails:
                answer_parts.append(f"Email: {emails[0]}")
            if phones:
                answer_parts.append(f"Phone: {phones[0]}")
            pairs.append({
                "question": "How can I contact you?",
                "expected_answer": ". ".join(answer_parts),
                "category": "contact",
                "difficulty": "easy",
            })

        # General topic question
        if len(content) > 100:
            first_sentence = content.split(".")[0] + "."
            pairs.append({
                "question": f"Tell me about your {topic.lower()}",
                "expected_answer": first_sentence[:200],
                "category": topic.lower().replace(" ", "_"),
                "difficulty": "medium",
            })

    # Deduplicate by question
    seen = set()
    unique = []
    for p in pairs:
        q = p["question"].lower()
        if q not in seen:
            seen.add(q)
            unique.append(p)

    return unique[:num_questions]


# ═══ Storage ═════════════════════════════════════════════════════════════════

def save_knowledge(entries: List[Dict], business_name: str = ""):
    """Save harvested entries to knowledge.json, merging with existing."""
    os.makedirs(DATA_DIR, exist_ok=True)

    existing = {"knowledge_base": [], "business_name": business_name or "Your Business"}
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE) as f:
            existing = json.load(f)

    if business_name:
        existing["business_name"] = business_name

    # Merge: avoid exact duplicate topics
    existing_topics = {e["topic"].lower() for e in existing["knowledge_base"]}
    added = 0
    for entry in entries:
        if entry["topic"].lower() not in existing_topics:
            existing["knowledge_base"].append(entry)
            existing_topics.add(entry["topic"].lower())
            added += 1
        else:
            # Update existing with newer/longer content
            for i, e in enumerate(existing["knowledge_base"]):
                if e["topic"].lower() == entry["topic"].lower():
                    if len(entry.get("content", "")) > len(e.get("content", "")):
                        existing["knowledge_base"][i] = entry
                        added += 1
                    break

    existing["updated_at"] = datetime.now().isoformat()

    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\n  💾 Saved {added} new/updated topics to {KNOWLEDGE_FILE}")
    print(f"     Total knowledge base: {len(existing['knowledge_base'])} topics")


def save_qa(qa_pairs: List[Dict], business_name: str = ""):
    """Save generated Q&A pairs to test_qa.json."""
    os.makedirs(DATA_DIR, exist_ok=True)

    data = {
        "business_name": business_name or "Your Business",
        "test_pairs": qa_pairs,
        "total_questions": len(qa_pairs),
        "categories": list(set(q.get("category", "general") for q in qa_pairs)),
        "generated_at": datetime.now().isoformat(),
    }

    with open(TEST_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  💾 Saved {len(qa_pairs)} Q&A pairs to {TEST_FILE}")


def log_harvest(method: str, source: str, entries_count: int):
    """Log harvest activity."""
    os.makedirs(DATA_DIR, exist_ok=True)

    log = []
    if os.path.exists(HARVEST_LOG):
        with open(HARVEST_LOG) as f:
            log = json.load(f)

    log.append({
        "method": method,
        "source": source,
        "entries": entries_count,
        "timestamp": datetime.now().isoformat(),
    })

    with open(HARVEST_LOG, "w") as f:
        json.dump(log, f, indent=2)


def show_status():
    """Show collected data statistics."""
    print(f"\n{'═' * 55}")
    print(f"  OnboardAI — Harvest Status")
    print(f"{'═' * 55}")

    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE) as f:
            kb = json.load(f)
        entries = kb.get("knowledge_base", [])
        total_chars = sum(len(e.get("content", "")) for e in entries)
        print(f"\n  Business:    {kb.get('business_name', '?')}")
        print(f"  Topics:      {len(entries)}")
        print(f"  Total chars: {total_chars:,}")

        # Sources
        sources = {}
        for e in entries:
            if "source_url" in e:
                src = "website"
            elif "source_file" in e:
                src = "document"
            elif e.get("source") == "interview":
                src = "interview"
            else:
                src = "other"
            sources[src] = sources.get(src, 0) + 1

        print(f"\n  Sources:")
        for src, count in sorted(sources.items()):
            print(f"    {src:12s}  {count} topics")
    else:
        print(f"\n  No knowledge base yet. Run a harvest method first.")

    if os.path.exists(TEST_FILE):
        with open(TEST_FILE) as f:
            qa = json.load(f)
        print(f"\n  Test Q&A:    {qa.get('total_questions', 0)} questions")
        print(f"  Categories:  {', '.join(qa.get('categories', []))}")
    else:
        print(f"\n  No test Q&A yet. Run: python harvest.py --generate-qa")

    if os.path.exists(HARVEST_LOG):
        with open(HARVEST_LOG) as f:
            log = json.load(f)
        print(f"\n  Harvest log: {len(log)} operations")
        for entry in log[-5:]:
            print(f"    [{entry['method']:10s}] {entry['entries']} entries from "
                  f"{entry.get('source', '?')[:40]}")

    print(f"\n{'═' * 55}\n")


# ═══ CLI ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🏢 OnboardAI — Business Data Harvester"
    )
    parser.add_argument("--url", type=str, help="Scrape a business website")
    parser.add_argument("--depth", type=int, default=1,
                        help="Crawl depth for website scraping (default: 1)")
    parser.add_argument("--max-pages", type=int, default=15,
                        help="Max pages to scrape (default: 15)")
    parser.add_argument("--docs", type=str,
                        help="Parse documents from a directory or file")
    parser.add_argument("--interview", action="store_true",
                        help="Run guided interview questionnaire")
    parser.add_argument("--generate-qa", action="store_true",
                        help="Generate Q&A test pairs from collected knowledge")
    parser.add_argument("--num-qa", type=int, default=20,
                        help="Number of Q&A pairs to generate (default: 20)")
    parser.add_argument("--business-name", type=str, default="",
                        help="Business name (auto-detected from website if not set)")
    parser.add_argument("--status", action="store_true",
                        help="Show harvested data statistics")

    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    if args.status:
        show_status()
        return

    if args.url:
        entries = scrape_website(args.url, max_pages=args.max_pages, depth=args.depth)
        if entries:
            # Auto-detect business name from first page title
            biz_name = args.business_name
            if not biz_name and entries:
                biz_name = entries[0].get("topic", "").split("-")[0].strip()
            save_knowledge(entries, business_name=biz_name)
            log_harvest("website", args.url, len(entries))
        else:
            print("  ⚠️  No content extracted from website.")

    elif args.docs:
        entries = parse_documents(args.docs)
        if entries:
            save_knowledge(entries, business_name=args.business_name)
            log_harvest("documents", args.docs, len(entries))
        else:
            print("  ⚠️  No documents parsed.")

    elif args.interview:
        entries = run_interview()
        if entries:
            save_knowledge(entries, business_name=args.business_name)
            log_harvest("interview", "stdin", len(entries))

    elif args.generate_qa:
        if not os.path.exists(KNOWLEDGE_FILE):
            print("  ❌ No knowledge base. Run --url, --docs, or --interview first.")
            sys.exit(1)

        with open(KNOWLEDGE_FILE) as f:
            knowledge = json.load(f)

        qa_pairs = generate_qa_pairs(
            knowledge["knowledge_base"],
            num_questions=args.num_qa
        )
        if qa_pairs:
            save_qa(qa_pairs, business_name=knowledge.get("business_name", ""))
            log_harvest("qa-generation", "knowledge_base", len(qa_pairs))
        else:
            print("  ⚠️  No Q&A pairs generated.")
    else:
        parser.print_help()
        print("\n  💡 Quick start:")
        print("     python harvest.py --url https://your-business.com")
        print("     python harvest.py --generate-qa")
        print("     python evaluate.py --verbose\n")


if __name__ == "__main__":
    main()
