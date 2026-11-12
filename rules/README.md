# Rule library

One rule per `.yaml` file, in the folder for its lens: `fairness/`, `respect/`, or `access/`.
File name: the rule id in lowercase, for example `fair-age-001.yaml`.

## Fields

| Field | Required | What it holds |
|---|---|---|
| `id` | yes | `LENS-CATEGORY-NNN`, for example `FAIR-AGE-001`. Must be unique. |
| `lens` | yes | `fairness`, `respect`, or `access` |
| `category` | yes | The taxonomy category, in plain words |
| `severity` | yes | `high`, `medium`, or `low` |
| `match_type` | yes | `phrase` (whole-word list), `regex` (pattern), or `metric` (a number check) |
| `patterns` | phrase and regex | List of phrases or regex patterns |
| `metric`, `threshold` | metric | Which number to check and the limit. v1 supports `sentence_words`. |
| `case_sensitive` | no | `true` if case matters (the ALL-CAPS rule). Default: ignore case. |
| `applies_to` | yes | Any of `hiring`, `decisions`, `education`, `customer_service`, `communications`, or `all` |
| `why` | yes | One plain sentence a non-expert understands |
| `who_is_affected` | yes | The people this language harms |
| `suggestion` | yes | What to say instead |
| `limitations` | no | When the rule can be wrong and a person should check (brief, section 6.5) |
| `source_title`, `source_url` | yes | The primary source |
| `examples.should_flag`, `examples.should_not_flag` | yes | At least one each. pytest runs them. |

## Adding a rule

1. Copy an existing rule file and give it a new id.
2. Fill in every field. Test any regex on regex101.com (Python flavor) first.
3. Run `pytest`. Commit when everything passes.

Rules never flag an identity term on its own. A term is a flag only inside a pattern that excludes, demeans, or screens.
