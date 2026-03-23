# Hardcode Optimization Plan

## Strategy: Hardcode Everything, LLM Only for Edge Cases

**Goal**: Make 90%+ of responses instant by hardcoding patterns. Only use LLM when:
- Grammatical/spelling errors prevent hardcoded matching
- Truly ambiguous requests
- Complex natural language generation (analysis summaries)

---

## Current LLM Usage Analysis

### ✅ Already Hardcoded (Fast Path)
1. **Greetings** - Instant responses (<0.01s)
2. **Help requests** - Instant responses
3. **Thank you** - Instant responses
4. **Request type detection** - 90% keyword-based, LLM only for ambiguous cases
5. **Symbol extraction** - Regex + company name mapping, LLM only as fallback

### ⚠️ Can Be Hardcoded (Should Optimize)

#### 1. Status Messages (Line 122, 142-187)
**Current**: LLM generates status messages for every request
**Problem**: Adds 5-30s delay before actual work starts
**Solution**: Hardcode all status messages

```python
STATUS_MESSAGES = {
    "stock_screening": "🔍 Screening stocks based on your criteria. This may take a few minutes...",
    "stock_data": "📥 Downloading stock data. Please wait...",
    "stock_analysis": "📊 Analyzing stock performance. Gathering data...",
    "financial_analysis": "💼 Performing financial analysis. This may take a moment...",
    "general": "🤔 Processing your request..."
}
```

**Impact**: Saves 5-30s per request

#### 2. Symbol Extraction - Fuzzy Matching (Line 933-992)
**Current**: Uses LLM if regex fails
**Problem**: Misspellings trigger LLM (e.g., "Appel" instead of "Apple")
**Solution**: Add fuzzy string matching before LLM

```python
from difflib import get_close_matches

# Fuzzy match company names with typos
company_names = list(company_to_symbol.keys())
user_words = user_input.lower().split()
for word in user_words:
    matches = get_close_matches(word, company_names, n=1, cutoff=0.7)
    if matches:
        symbol = company_to_symbol[matches[0]]
        # Found match with typo tolerance
```

**Impact**: Handles 80%+ of typos without LLM

#### 3. Request Type Detection - Expand Keywords (Line 258-335)
**Current**: Good keyword coverage, but can expand
**Solution**: Add more variations and common misspellings

```python
# Add common misspellings
screening_keywords = [
    'screen', 'screening', 'scren', 'screeen',  # typos
    'find good stocks', 'find undervalued', 
    'undervalued stocks', 'undervalued stock',  # singular/plural
    # ... more variations
]
```

**Impact**: Reduces LLM calls from ~10% to ~2%

#### 4. Sector Extraction - Hardcode Mapping (Line 543+)
**Current**: Uses LLM to extract sectors
**Solution**: Hardcode sector keywords and aliases

```python
SECTOR_KEYWORDS = {
    'technology': ['tech', 'technology', 'software', 'hardware', 'it'],
    'healthcare': ['healthcare', 'health', 'medical', 'pharma', 'biotech'],
    'finance': ['finance', 'financial', 'banking', 'banks', 'fintech'],
    # ... all sectors
}
```

**Impact**: Eliminates LLM calls for sector extraction

---

### 🔴 Needs LLM (Keep These)

#### 1. Analysis Generation (Line 682, 725)
**Why**: Natural language summaries require LLM
**When**: Only for complex analysis, not simple data queries
**Optimization**: Template simple cases, LLM for complex

#### 2. Catalyst Search (fifth_layer_screening.py)
**Why**: Needs to understand news/context
**When**: Only for screening operations
**Optimization**: Can reduce frequency (only top 5 stocks)

#### 3. Truly Ambiguous Requests
**Why**: Can't be parsed with keywords/fuzzy matching
**When**: <2% of requests
**Optimization**: Use fast, cheap LLM (local or OpenRouter)

---

## Optimization Priority

### Phase 1: Quick Wins (90% speed improvement)
1. ✅ Hardcode status messages (5-30s saved per request)
2. ✅ Add fuzzy matching for symbols (handles typos)
3. ✅ Expand keyword lists (reduces ambiguous cases)

**Result**: 90%+ requests become instant or near-instant

### Phase 2: Advanced Hardcoding
1. Hardcode sector extraction
2. Template simple analysis responses
3. Add more company name variations

**Result**: 95%+ requests instant

### Phase 3: LLM Optimization
1. Only use LLM for truly complex cases
2. Choose optimal LLM (local vs OpenRouter)

---

## Local vs OpenRouter for Edge Cases

### Edge Case Characteristics:
- **Low volume**: Only 2-5% of requests
- **Need fast response**: User already frustrated (typo/error)
- **Need good understanding**: Handle misspellings/grammar errors
- **Simple tasks**: Classification, extraction, not generation

### Recommendation: **OpenRouter** for Edge Cases

**Why OpenRouter:**
1. **Speed**: 1-3s vs 5-30s (critical for frustrated users)
2. **Better at typos**: Claude 3.5 Sonnet handles misspellings better
3. **Low cost**: 2-5% of requests × $0.001 = ~$0.0001 per request
4. **Reliability**: No local model loading delays

**Why NOT Local:**
1. **Too slow**: 5-30s wait for edge cases is frustrating
2. **Worse at typos**: Smaller model struggles with misspellings
3. **Memory overhead**: Loading model just for 2% of requests

### Hybrid Approach (Best of Both):

```python
# Use OpenRouter for edge cases (fast, accurate)
if needs_llm_for_edge_case:
    use_openrouter()  # Fast, handles typos well

# Use Local LLM for heavy analysis (if you want to save costs)
if needs_complex_analysis:
    use_local_llm()  # Free, but slower (acceptable for long operations)
```

---

## Implementation Strategy

### Step 1: Hardcode Everything Possible
- Status messages
- Fuzzy matching
- Expanded keywords
- Sector mapping

### Step 2: Add Typo Tolerance
- Fuzzy string matching
- Common misspellings dictionary
- Phonetic matching (optional)

### Step 3: LLM Fallback Logic
```python
def needs_llm(user_input, extracted_data):
    # Only use LLM if:
    # 1. Can't extract symbols (even with fuzzy matching)
    # 2. Can't determine request type (even with expanded keywords)
    # 3. Truly ambiguous request
    
    if extracted_data['symbols'] or extracted_data['request_type']:
        return False  # Don't need LLM
    
    # Check if input has typos/errors
    if has_obvious_typos(user_input):
        return True  # Use LLM to handle typos
    
    return False  # Hardcoded path should work
```

### Step 4: Choose LLM Provider
- **Edge cases**: OpenRouter (fast, accurate)
- **Heavy analysis**: Your choice (local = free but slow, OpenRouter = fast but costs)

---

## Expected Results

### Before Optimization:
- Average response: 10-60 seconds
- LLM calls: 2-5 per request
- User experience: Slow, frustrating

### After Optimization:
- Average response: <1 second (90% of requests)
- LLM calls: 0-1 per request (only edge cases)
- User experience: Fast, responsive

### Cost Impact:
- **Before**: Many LLM calls (expensive if OpenRouter)
- **After**: Minimal LLM calls (2-5% of requests)
- **Cost**: ~$0.0001 per request (vs $0.01-0.05 before)

---

## Conclusion

**Hardcode everything possible** → Use LLM only for:
1. Typos/grammar errors that prevent matching
2. Truly ambiguous requests
3. Complex natural language generation

**For edge cases**: Use **OpenRouter** (fast, accurate, low cost)

**Result**: 90%+ instant responses, minimal LLM usage, great UX!




