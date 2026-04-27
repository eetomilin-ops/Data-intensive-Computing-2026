# Code style ruleset

## Goal
Produce code that resembles typical human-written software rather than AI-generated output. Avoid patterns that signal templated, overly generic, or instructional code.

### Heading style
Use sentence case for markdown headings and comment titles. Capitalize only the first word and proper nouns.
---
## Dos

### 1. Write purposeful, non-obvious comments
Comment **why**, not **what**. Focus on intent, trade-offs, constraints, or edge cases.
Good sample
```
# Avoid division by zero when baseline data is incomplete
if base == 0: return None
```

### 2. Use inconsistent (natural) comment density
Comment only where needed. Leave some obvious lines uncommented.

### 3. Reflect real-world constraints
Add domain-specific handling instead of generic fallbacks. Encode assumptions explicitly.

Good sample
```
# Expect values in percentage format (0–100)
if value > 100: raise ValueError("Unexpected scale")
```

### 4. Vary function and variable naming
Mix concise and descriptive names.Avoid overly systematic naming patterns.

Good sample
```
parseYear()
clean_val()
normalizeBaseline()
```

### 5. Allow minor imperfections
Small asymmetries in structure are acceptable.Humans rarely write perfectly uniform code.

### 6. Use context-specific error handling
Tailor logic to expected data issues. Avoid generic “catch-all” patterns.
Avoid guards where possible. Fail fast. Aim for speed.

### 7. Write selective docstrings
Avoid general docstrings, use only for non-trivial functions. Include edge cases or assumptions if relevant.
Use common comments for outher cases. 

Good sample
```
def normalize(series):
    """Normalize relative to first valid entry; assumes sorted input."""
````

### 8. Use signature comments for function specs
For planned or stubbed typed functions, use a short comment above the function and inline comments for arguments and return value.
Align all inline comments in that signature block to the longest pre-comment signature line plus 4 spaces.

Good sample
```python
# build one stopword lookup for the tokenizer stage
def load_stopwords(
    stopwords_path: str | Path,   # source file with one word per line
) -> set[str]:                    # lookup used during token filtering
```

### 9. Separate block and expression comments
Use inline comments for expressions only, after 4 spaces.
Use a short comment above code blocks such as functions, loops, try blocks, and condition groups.
When several inline comments appear in one block, align them to the longest expression where practical.

Good sample
```python
value = scale(raw)    # normalize before ranking

# loop once and keep the local aggregate small
for key in items:
    short = a + b          # first partial score
    wider_name = c + d     # second partial score
```

### 10. Mix coding styles slightly
Minor variation in formatting or structure is acceptable. Avoid rigid, repeated templates.

### 12. Use impersonal voice in comments
Avoid first-person pronouns such as "we", "I", or "our" in comments. Use indirect or passive constructions instead.

Good
```python
# one heap per category, filled as each term group is processed
```
Bad
```python
# one heap per category, filled as we process each term group
```

### 11. Use compact single-line guards
Write single-statement conditionals on one line. No blank line before or after guard blocks.

Good
```python
if x is None: return
if denom == 0: return 0.0
```
Bad
```python
if x is None:
    return

if denom == 0:
    return 0.0
```

---

## Don'ts
1. Do not explain obvious code. Avoid comments that restate the code.
Bad sample
```
# Create a list of columns
cols = list(df.columns)
```

### 2. Do not use template-like docstrings everywhere
Avoid uniform phrasing across all functions. Do not describe trivial behavior.
Bad sample 
```
"""Convert input to float or return None."""
```
### 3. Avoid canonical AI pipelines
Repetitive patterns like: strip → convert → coerce → fallback . Generic “safe” conversions without context .
Bad sample 
```
pd.to_numeric(str(x).strip(), errors="coerce")
```
### 4. Avoid overly defensive generic logic
Do not handle every possible case identically. Avoid “universal” fallback outputs like None or NaN without reasoning. Fail fast. Aim for speed and readability.

### 5. Do not narrate code usage
Avoid describing where or how code is used externally.
Bad sample
```
# This function is applied during CSV loading
```

### 6. Avoid excessive uniformity
Do not keep identical structure across all functions.
Avoid repeated patterns in: docstrings, comments, naming

### 7. Avoid over-clean mathematical formulations (weak)
Real code often includes intermediate variables or checks. Avoid overly “perfect” one-liners for complex logic. Avoid extra variables where possible.
Bad
return ((s / base) * 100).round(2)

### 8. Do not over-document simple helpers
Small utility functions typically have minimal or no documentation.

### 9. Optimize for readability.
Do not make uber one liners. Expression length is 60-100 symbols max. Do not add extra CRLF, make code compact. 

## Checklist
Before finalizing code, verify:
 - Comments explain intent, not syntax
 - Some parts are intentionally uncommented
 - Naming is not overly systematic
 - Error handling reflects real constraints
 - No repeated “AI-style” pipelines
 - Docstrings are sparse and non-uniform
 - Stubbed function specs use the multiline signature comment template
 - Inline signature comments are aligned to the widest signature line plus 4 spaces
 - Block comments sit above control structures and inline comments are kept for expressions
 - Single-statement guards are written on one line
 - Comments use impersonal voice, no "we" or "I"
 - Code is slightly irregular but still clear
