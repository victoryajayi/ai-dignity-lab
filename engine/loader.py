"""
loader.py: reads every rule file in rules/ and checks it is complete.

Each .yaml file holds one rule (see rules/README.md for the fields).
If a rule is broken, this file stops with a clear message that names
the file and the problem, so a bad rule never runs silently.
"""

import re
from pathlib import Path

import yaml

# The folder that holds the rules: <repo>/rules, found relative to this
# file so the engine works no matter which folder you run it from.
DEFAULT_RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

# Every rule must have these fields.
REQUIRED_FIELDS = [
    "id", "lens", "category", "severity", "match_type", "applies_to",
    "why", "who_is_affected", "suggestion", "source_title", "source_url",
    "examples",
]

# Allowed values for the fields that have a fixed list of options.
VALID_LENSES = {"fairness", "respect", "access"}
VALID_SEVERITIES = {"high", "medium", "low"}
VALID_MATCH_TYPES = {"phrase", "regex", "metric"}
VALID_CONTENT_TYPES = {
    "hiring", "decisions", "education", "customer_service",
    "communications", "all",
}
VALID_METRICS = {"sentence_words"}


class RuleError(ValueError):
    """Raised when a rule file is missing a field or has a bad value."""


def load_rules(rules_dir=DEFAULT_RULES_DIR):
    """Load every rule under rules_dir and return them as a list of dicts."""
    rules_path = Path(rules_dir)
    if not rules_path.is_dir():
        raise RuleError(f"Rules folder not found: {rules_path}")

    rules = []
    seen_ids = {}  # rule id -> file it came from, to catch duplicates

    # rglob finds .yaml files in every subfolder (fairness/, respect/, ...).
    # sorted() keeps the order the same on every computer.
    for file in sorted(rules_path.rglob("*.yaml")):
        with file.open(encoding="utf-8") as f:
            rule = yaml.safe_load(f)  # safe_load never runs code from the file

        validate_rule(rule, file)

        if rule["id"] in seen_ids:
            raise RuleError(
                f"{file.name}: id {rule['id']} is already used in "
                f"{seen_ids[rule['id']].name}"
            )
        seen_ids[rule["id"]] = file
        rules.append(rule)

    if not rules:
        raise RuleError(f"No .yaml rule files found in {rules_path}")
    return rules


def validate_rule(rule, file):
    """Check one rule. Raise RuleError with a plain message if anything is wrong."""
    name = Path(file).name

    if not isinstance(rule, dict):
        raise RuleError(f"{name}: the file is empty or not a single YAML rule")

    missing = [field for field in REQUIRED_FIELDS if field not in rule]
    if missing:
        raise RuleError(f"{name}: missing field(s): {', '.join(missing)}")

    if rule["lens"] not in VALID_LENSES:
        raise RuleError(f"{name}: lens must be one of {sorted(VALID_LENSES)}")
    if rule["severity"] not in VALID_SEVERITIES:
        raise RuleError(f"{name}: severity must be one of {sorted(VALID_SEVERITIES)}")
    if rule["match_type"] not in VALID_MATCH_TYPES:
        raise RuleError(f"{name}: match_type must be one of {sorted(VALID_MATCH_TYPES)}")

    bad_types = set(rule["applies_to"]) - VALID_CONTENT_TYPES
    if bad_types:
        raise RuleError(f"{name}: unknown applies_to value(s): {sorted(bad_types)}")

    # Phrase and regex rules need a list of patterns.
    if rule["match_type"] in {"phrase", "regex"}:
        patterns = rule.get("patterns")
        if not patterns or not isinstance(patterns, list):
            raise RuleError(f"{name}: a {rule['match_type']} rule needs a 'patterns' list")
        if rule["match_type"] == "regex":
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as err:
                    raise RuleError(f"{name}: bad regex {pattern!r}: {err}") from err

    # Metric rules need to name the metric and a threshold number.
    if rule["match_type"] == "metric":
        if rule.get("metric") not in VALID_METRICS:
            raise RuleError(f"{name}: metric must be one of {sorted(VALID_METRICS)}")
        if not isinstance(rule.get("threshold"), (int, float)):
            raise RuleError(f"{name}: a metric rule needs a numeric 'threshold'")

    # Quality bar (brief, section 6.5): at least one example of each kind.
    examples = rule["examples"] or {}
    for kind in ("should_flag", "should_not_flag"):
        if not examples.get(kind):
            raise RuleError(f"{name}: examples.{kind} needs at least one example")
