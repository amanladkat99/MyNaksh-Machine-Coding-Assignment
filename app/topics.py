"""Shared vocabulary"""
import re

# topic/category -> keywords that signal it in a question
TOPIC_KEYWORDS = {
    "career": r"career|job|jobs|work|profession|promotion|business|startup|office|salary|employer|company|role",
    "relationship": r"love|marriage|marry|married|wedding|partner|relationship|spouse|dating",
    "finance": r"money|finance|financial|invest|investment|wealth|income|savings|property|house|loan",
    "health": r"health|fitness|diet|weight|illness|surgery|exercise",
    "interest": r"hobby|hobbies|interest|interests|passion|enjoy",
}

# Words that indicate a goal / plan inside a statement
GOAL_WORDS = (
    r"\b(plan\w*|want\w*|hope|hoping|aim\w*|goal|switch\w*|chang\w*|quit\w*|"
    r"leav\w*|start\w*|look\w* for|get\w*|going to|dream\w*|wish\w*|need)\b"
)

# Keywords that mark a statement as a goal for a given topic
GOAL_TOPICS = {
    "career": r"job|jobs|career|promotion|business|startup|company|profession|role|position|work",
    "relationship": r"marry|married|marriage|wedding|relationship|partner",
    "finance": r"invest\w*|buy|save|savings|house|property|loan|money",
    "health": r"weight|fitness|health|diet|surgery|exercise",
}

NEGATION = re.compile(r"\b(don't|do not|doesn't|never|no longer|not)\b", re.I)

LANGUAGES = (
    "hindi|english|tamil|telugu|marathi|bengali|gujarati|punjabi|kannada|"
    "malayalam|urdu|spanish|french|german"
)

# "What do you remember about me?" style questions
RECALL_PATTERN = re.compile(
    r"\b(remember|recall|know about me|do you know|what did i (tell|say))\b", re.I
)

# Generic words ignored when matching question words against memory text
STOPWORDS = {
    "what", "should", "about", "with", "this", "that", "have", "from", "your",
    "will", "would", "could", "there", "their", "which", "when", "where", "why",
    "does", "next", "year", "tell", "please", "focus",
}


def detect_topics(text: str) -> set:
    """Return the set of topics mentioned in `text`."""
    return {
        topic
        for topic, pattern in TOPIC_KEYWORDS.items()
        if re.search(rf"\b({pattern})\b", text, re.I)
    }
