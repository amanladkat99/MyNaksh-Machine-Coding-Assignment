# Personalized AI Chat

FastAPI chat service with session history and long-term user memory (SQLite).

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment variables (via .env file or shell export)
cp .env.example .env
# Edit .env and set LLM_API_KEY (plus optional LLM_BASE_URL, LLM_MODEL, DB_PATH)

uvicorn app.main:app --reload
```
Without `LLM_API_KEY` the service still works using a rule-based fallback reply (`fallback: true`).

## Tests (mock LLM)
```bash
pytest -v
```

## Architecture
```
app/main.py       FastAPI routes (POST /chat, GET /memories/{user_id})
app/service.py    Orchestration: extract -> retrieve -> prompt -> LLM -> save
app/extractor.py  MemoryExtractor: rule-based extraction of goals, preferences & facts
app/store.py      MemoryStore: SQLite persistence & upserts for user memories
app/retriever.py  MemoryRetriever: topic & keyword-based relevant memory selection
app/topics.py     Shared topic keyword vocabularies and topic detection
app/models.py     Memory dataclass
app/history.py    HistoryStore: last-N messages per session
app/llm.py        LLMClient interface + OpenAI-compatible implementation
app/db.py         SQLite schema and connection helper
app/config.py     Environment-driven settings
```

### Memory storage
Table `memories(user_id, key, category, value, confidence)` with `UNIQUE(user_id, key)`.
Rule-based extraction stores only goals/plans, language preference, interests and personal
facts (name, birth info, occupation). Questions and small talk are ignored.
Negated statements ("I don't want to switch jobs") are not stored.
Re-stating a fact with the same key (e.g. `career_goal`) **overwrites** it, so corrections work.
Each rule assigns a confidence score used for ranking.

### Memory retrieval
1. Detect topics in the question via keyword lists (career, relationship, finance, health, interest).
2. Select memories whose category matches, plus `language_preference` (always shapes the reply),
   plus memories sharing meaningful keywords with the question.
3. "What do you remember...?" returns everything (or only the topic asked about).
4. Top 5 by confidence go in the system prompt. A career question never includes interests.

### History
The last 6 messages of the session are sent to the LLM.

### Trade-offs
- Rules are simple and deterministic but miss unusual phrasing; an LLM extractor could replace
  `MemoryExtractor` behind the same interface.
- Keyword retrieval is cheap and explainable; embeddings would improve recall.
- Fallback when the LLM is down: response built from relevant memories, `fallback: true`.

## Sample API Request & Response

`POST /chat`

Request:
```json
{
  "user_id": "user-123",
  "session_id": "session-456",
  "message": "What should I focus on for my career?"
}
```

Response:
```json
{
  "user_id": "user-123",
  "session_id": "session-456",
  "response": "आपके अगले साल नौकरी बदलने के लक्ष्य को देखते हुए अपने कौशल और नेटवर्किंग पर ध्यान दें।",
  "context_used": ["language_preference", "career_goal"],
  "fallback": false
}
```
