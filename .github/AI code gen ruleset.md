# Code Style Ruleset

## Goal
Produce code that resembles typical human-written software rather than AI-generated output. Avoid patterns that signal templated, overly generic, or instructional code.
---
## DOs

### 1. Write Purposeful, Non-Obvious Comments
Comment **why**, not **what**. Focus on intent, trade-offs, constraints, or edge cases.
Good sample
```
# Avoid division by zero when baseline data is incomplete
if base == 0: return None
```

### 2. Use Inconsistent (Natural) Comment Density
Comment only where needed. Leave some obvious lines uncommented.

### 3. Reflect Real-World Constraints
Add domain-specific handling instead of generic fallbacks. Encode assumptions explicitly.

Good sample
```
# Expect values in percentage format (0–100)
if value > 100: raise ValueError("Unexpected scale")
```

### 4. Vary Function and Variable Naming
Mix concise and descriptive names.Avoid overly systematic naming patterns.

Good sample
```
parseYear()
clean_val()
normalizeBaseline()
```

### 5. Allow Minor Imperfections
Small asymmetries in structure are acceptable.Humans rarely write perfectly uniform code.

### 6. Use Context-Specific Error Handling
Tailor logic to expected data issues. Avoid generic “catch-all” patterns.
Avoid guards where possible. Fail fast. Aim for speed.

### 7. Write Selective Docstrings
Avoid general docstrings, use only for non-trivial functions. Include edge cases or assumptions if relevant.
Use common comments for outher cases. 

Good sample
```
def normalize(series):
    """Normalize relative to first valid entry; assumes sorted input."""
````

### 8. Use Signature Comments for Function Specs
For planned or stubbed typed functions, use a short comment above the function and inline comments for purpose, arguments, and return value.
Align all inline comments in that signature block to the longest pre-comment signature line plus 4 spaces.

Good sample
```python
# build one stopword lookup for the tokenizer stage
def load_stopwords(               # parse normalized stopwords from file
    stopwords_path: str | Path,   # source file with one word per line
) -> set[str]:                    # lookup used during token filtering
```

### 9. Mix Coding Styles Slightly
Minor variation in formatting or structure is acceptable. Avoid rigid, repeated templates.

---

## DON'Ts
1. Do Not Explain Obvious Code . Avoid comments that restate the code.
Bad sample
```
# Create a list of columns
cols = list(df.columns)
```

### 2. Do Not Use Template-Like Docstrings Everywhere
Avoid uniform phrasing across all functions. Do not describe trivial behavior.
Bad sample 
```
"""Convert input to float or return None."""
```
### 3. Avoid Canonical AI Pipelines
Repetitive patterns like: strip → convert → coerce → fallback . Generic “safe” conversions without context .
Bad sample 
```
pd.to_numeric(str(x).strip(), errors="coerce")
```
### 4. Avoid Overly Defensive Generic Logic
Do not handle every possible case identically. Avoid “universal” fallback outputs like None or NaN without reasoning. Fail fast. Aim for speed and readability.

### 5. Do Not Narrate Code Usage
Avoid describing where or how code is used externally.
Bad sample
```
# This function is applied during CSV loading
```

### 6. Avoid Excessive Uniformity
Do not keep identical structure across all functions.
Avoid repeated patterns in: docstrings, comments, naming

### 7. Avoid Over-Clean Mathematical Formulations (weak)
Real code often includes intermediate variables or checks. Avoid overly “perfect” one-liners for complex logic. Avoid extra variables where possible.
Bad
return ((s / base) * 100).round(2)

### 8. Do Not Over-Document Simple Helpers
Small utility functions typically have minimal or no documentation.

### 9. Optimize for readability .
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
 - Code is slightly irregular but still clear
