"""
matchers.py: runs the rules against a piece of text and returns flags.

How it works:
1. The text is cleaned up (curly quotes become straight quotes).
2. It is split into sentences, so every flag can show its sentence.
3. Each rule is turned into one regular expression (or a metric check)
   and run on every sentence.
4. Each match becomes a Flag holding everything a Rule Card needs.
"""

import re
from dataclasses import dataclass

# Sort order for the output: high first, then medium, then low.
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# A sentence ends at . ! or ? followed by a space, or at a line break.
# Line breaks count because job postings often use bullet lines with no period.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

# A "word" for counting: letters/digits, allowing ' and - inside (don't, full-time).
WORD = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")


@dataclass
class Flag:
    """One problem found in the text: everything a Rule Card shows."""
    rule_id: str
    lens: str
    category: str
    severity: str
    matched_text: str
    sentence: str
    why: str
    who_is_affected: str
    suggestion: str
    source_title: str
    source_url: str
    limitations: str = ""


def normalize(text):
    """Swap curly quotes for straight ones so patterns match either style."""
    return (
        text.replace("\u2019", "'").replace("\u2018", "'")
        .replace("\u201c", '"').replace("\u201d", '"')
    )


def split_sentences(text):
    """Return the text as a list of non-empty sentences."""
    parts = SENTENCE_SPLIT.split(normalize(text))
    return [part.strip() for part in parts if part.strip()]


def phrase_to_regex(phrase):
    r"""
    Turn a plain phrase into a whole-word regex.
    'digital native' -> \bdigital\s+native\b
    \b means "word boundary", so 'native' will not match inside 'nativeness'.
    \s+ lets the words be separated by any spaces or a line break.
    re.escape makes characters like - or . count literally.
    """
    words = [re.escape(word) for word in phrase.split()]
    return r"\b" + r"\s+".join(words) + r"\b"


def compile_rule(rule):
    """Combine all of a rule's patterns into one regex, longest first."""
    if rule["match_type"] == "phrase":
        pieces = [phrase_to_regex(p) for p in rule["patterns"]]
    else:  # regex rules are written as regex already
        pieces = list(rule["patterns"])

    # Longest first, so 'no childcare obligations' wins over a shorter overlap.
    pieces.sort(key=len, reverse=True)
    combined = "|".join(f"(?:{piece})" for piece in pieces)

    # Matching ignores case unless the rule says case matters (ALL-CAPS rule).
    flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
    return re.compile(combined, flags)


def rule_applies(rule, content_type):
    """True if the rule should run on this content type."""
    if content_type is None:  # no type given: run every rule
        return True
    applies_to = rule["applies_to"]
    return "all" in applies_to or content_type in applies_to


def make_flag(rule, matched_text, sentence):
    """Build a Flag from a rule and the text it matched."""
    return Flag(
        rule_id=rule["id"],
        lens=rule["lens"],
        category=rule["category"],
        severity=rule["severity"],
        matched_text=matched_text,
        sentence=sentence,
        why=" ".join(rule["why"].split()),          # tidy YAML line breaks
        who_is_affected=rule["who_is_affected"],
        suggestion=" ".join(rule["suggestion"].split()),
        source_title=rule["source_title"],
        source_url=rule["source_url"],
        limitations=" ".join(rule.get("limitations", "").split()),
    )


def check_metric(rule, sentence):
    """Run a metric rule on one sentence. Return a Flag or None."""
    if rule["metric"] == "sentence_words":
        word_count = len(WORD.findall(sentence))
        if word_count > rule["threshold"]:
            return make_flag(rule, f"{word_count} words", sentence)
    return None


def check_text(text, rules, content_type=None):
    """Run every applicable rule on the text. Return flags, most severe first."""
    flags = []
    sentences = split_sentences(text)

    for rule in rules:
        if not rule_applies(rule, content_type):
            continue

        if rule["match_type"] == "metric":
            for sentence in sentences:
                flag = check_metric(rule, sentence)
                if flag:
                    flags.append(flag)
            continue

        pattern = compile_rule(rule)
        for sentence in sentences:
            for match in pattern.finditer(sentence):
                flags.append(make_flag(rule, match.group(0), sentence))

    # Stable sort: severity first; ties keep the order they were found in.
    flags.sort(key=lambda flag: SEVERITY_ORDER[flag.severity])
    return flags
