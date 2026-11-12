"""
test_rules.py: turns every rule's examples into automated tests.

For each rule:
- every should_flag example must produce a flag from that rule
- every should_not_flag example must produce no flag from that rule
Add a rule with examples and pytest tests it automatically.
"""

import pytest

from engine.loader import RuleError, load_rules
from engine.matchers import check_text

RULES = load_rules()
RULES_BY_ID = {rule["id"]: rule for rule in RULES}

# One (rule id, example sentence) pair per test.
SHOULD_FLAG = [(r["id"], ex) for r in RULES for ex in r["examples"]["should_flag"]]
SHOULD_NOT_FLAG = [(r["id"], ex) for r in RULES for ex in r["examples"]["should_not_flag"]]


def flagged_by(rule_id, text):
    """True if this one rule flags the text. Content type is ignored here."""
    flags = check_text(text, [RULES_BY_ID[rule_id]])
    return any(flag.rule_id == rule_id for flag in flags)


@pytest.mark.parametrize("rule_id, example", SHOULD_FLAG)
def test_should_flag(rule_id, example):
    assert flagged_by(rule_id, example), f"{rule_id} missed: {example!r}"


@pytest.mark.parametrize("rule_id, example", SHOULD_NOT_FLAG)
def test_should_not_flag(rule_id, example):
    assert not flagged_by(rule_id, example), f"{rule_id} wrongly flagged: {example!r}"


def test_rule_ids_are_unique():
    ids = [rule["id"] for rule in RULES]
    assert len(ids) == len(set(ids))


def test_every_rule_has_a_source_link():
    for rule in RULES:
        assert rule["source_url"].startswith("https://"), rule["id"]


def test_content_type_filter_skips_rules_that_do_not_apply():
    # The age rule applies to hiring only, so it should not run on a customer reply.
    text = "We are looking for a digital native."
    hiring_ids = {f.rule_id for f in check_text(text, RULES, content_type="hiring")}
    service_ids = {f.rule_id for f in check_text(text, RULES, content_type="customer_service")}
    assert "FAIR-AGE-001" in hiring_ids
    assert "FAIR-AGE-001" not in service_ids


def test_broken_rule_gives_a_clear_error(tmp_path):
    # A rule missing most fields should stop the loader with a helpful message.
    (tmp_path / "bad.yaml").write_text("id: BAD-001\nlens: fairness\n")
    with pytest.raises(RuleError, match="missing field"):
        load_rules(tmp_path)
