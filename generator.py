import os
import json
import random
import anthropic

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def generate_question_paper(stream, subject, difficulty, marks, custom_topics="", bloom_levels=None):
    """
    Generate a structured question paper using Claude AI.
    Returns sections A, B, C with questions.
    Falls back to template-based generation if API fails.
    """
    if bloom_levels is None:
        bloom_levels = ["Remember", "Understand", "Apply", "Analyze"]

    # Determine section counts based on total marks
    if marks < 80:
        section_counts = {"A": 4, "B": 4, "C": 2}
    elif marks <= 120:
        section_counts = {"A": 5, "B": 4, "C": 3}
    else:
        section_counts = {"A": 6, "B": 5, "C": 4}

    difficulty_scales = {
        "Easy": {"b_marks": 5, "c_marks": 10},
        "Medium": {"b_marks": 6, "c_marks": 12},
        "Hard": {"b_marks": 8, "c_marks": 15}
    }
    scale = difficulty_scales.get(difficulty, difficulty_scales["Medium"])

    # Try AI generation first
    try:
        sections = _generate_with_ai(
            stream, subject, difficulty, marks,
            section_counts, scale, custom_topics, bloom_levels
        )
        return sections
    except Exception as e:
        print(f"AI generation failed: {e}. Falling back to templates.")
        return _generate_with_templates(stream, subject, difficulty, section_counts, scale)


def _generate_with_ai(stream, subject, difficulty, marks, section_counts, scale, custom_topics, bloom_levels):
    """Use Claude API to generate high-quality, unique questions."""

    topic_hint = f"Focus especially on: {custom_topics}." if custom_topics.strip() else ""
    bloom_hint = f"Use Bloom's taxonomy levels: {', '.join(bloom_levels)}." if bloom_levels else ""

    prompt = f"""You are an expert educator creating a university-level examination paper.

Generate a question paper with the following specifications:
- Stream: {stream}
- Subject: {subject}
- Difficulty: {difficulty}
- Total Marks: {marks}
{topic_hint}
{bloom_hint}

Create exactly:
- Section A: {section_counts['A']} Very Short Answer questions (2 marks each) — definitions, one-liners
- Section B: {section_counts['B']} Short Answer questions ({scale['b_marks']} marks each) — explanation, concepts
- Section C: {section_counts['C']} Long Answer questions ({scale['c_marks']} marks each) — analysis, design, case studies

Rules:
1. Questions must be UNIQUE, specific to {subject}, and educationally rigorous
2. No two questions should cover the same sub-topic
3. Section C questions should require critical thinking and multi-part answers
4. Questions should be exam-ready (clear, unambiguous)
5. For difficulty '{difficulty}': Easy=recall/basic, Medium=application, Hard=synthesis/evaluation

Return ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{{
  "A": {{
    "name": "Very Short Answer",
    "count": {section_counts['A']},
    "marks_per_q": 2,
    "questions": ["q1", "q2", ...]
  }},
  "B": {{
    "name": "Short Answer",
    "count": {section_counts['B']},
    "marks_per_q": {scale['b_marks']},
    "questions": ["q1", "q2", ...]
  }},
  "C": {{
    "name": "Long Answer",
    "count": {section_counts['C']},
    "marks_per_q": {scale['c_marks']},
    "questions": ["q1", "q2", ...]
  }}
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Clean up in case model returns markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()
    sections = json.loads(raw)
    return sections


def _generate_with_templates(stream, subject, difficulty, section_counts, scale):
    """Fallback template-based generation (original logic, improved)."""
    topic_map = {
        "Computer Science": ["algorithms", "data structures", "operating systems", "computer networks", "databases", "OOP", "software engineering"],
        "Engineering": ["thermodynamics", "mechanics", "materials science", "circuit analysis", "fluid dynamics", "structural analysis"],
        "Accounting": ["financial statements", "cost accounting", "budgeting", "taxation", "auditing", "ratio analysis"],
        "School": ["basic physics", "environmental science", "biology", "arithmetic", "chemistry", "geography"]
    }

    topics = topic_map.get(stream, [subject])
    random.shuffle(topics)

    templates = {
        "A": [
            "Define '{topic}' as used in {subject}.",
            "What is '{topic}'? Give a one-line definition.",
            "State the significance of '{topic}' in {subject}.",
            "List two key properties of '{topic}'.",
            "What do you understand by '{topic}'?",
            "Write the full form and meaning of '{topic}'.",
        ],
        "B": [
            "Explain '{topic}' with a suitable example from {subject}.",
            "Describe the working principle of '{topic}' in {subject}.",
            "Compare and contrast '{topic}' with its alternatives in {subject}.",
            "Outline the steps involved in implementing '{topic}' in {subject}.",
            "Discuss the advantages and limitations of '{topic}' in {subject}.",
        ],
        "C": [
            "Critically analyze the role of '{topic}' in modern {subject} applications. Support your answer with real-world case studies.",
            "Design a solution to a real-world problem using '{topic}'. Justify your design decisions.",
            "Evaluate the impact of '{topic}' on {subject}. Discuss both theoretical and practical perspectives.",
            "Compare different approaches to '{topic}' in {subject} and recommend the most suitable one with reasoning.",
        ]
    }

    sections = {}
    used_topics = []

    for section_key, count in section_counts.items():
        if section_key == "A":
            name = "Very Short Answer"
            marks_per_q = 2
        elif section_key == "B":
            name = "Short Answer"
            marks_per_q = scale["b_marks"]
        else:
            name = "Long Answer"
            marks_per_q = scale["c_marks"]

        questions = []
        for _ in range(count):
            available = [t for t in topics if t not in used_topics] or topics
            topic = random.choice(available)
            used_topics.append(topic)
            q = random.choice(templates[section_key]).format(subject=subject, topic=topic)
            questions.append(q)

        sections[section_key] = {
            "name": name,
            "count": count,
            "marks_per_q": marks_per_q,
            "questions": questions
        }

    return sections
