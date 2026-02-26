# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STORIUM Bot - KakaoTalk chatbot via 메신저봇R (Android JS app) providing 31+ commands: AI chat, finance, news, entertainment, utilities.

**Message Flow**: KakaoTalk → 메신저봇R (`메신저r.js`) → FastAPI `POST /api/kakaotalk` → `core/router.py:get_reply_msg()` → handlers → response

**Scheduled Messages**: `메신저r.js` polls `POST /api/poll` every 60s → `services/schedule_service.py` returns pending messages via APScheduler

## Common Commands

```bash
# Run server (port 8002)
python main_improved.py

# Install dependencies
pip install -r requirements.txt

# Install Playwright for movie rankings
playwright install chromium

# Test endpoint
curl -X POST http://localhost:8002/api/kakaotalk -H "Content-Type: application/json" -d '{"room":"test","sender":"test","msg":"/테스트"}'

# Run tests (no server needed, uses mocks)
python test_services.py     # Service layer tests
python test_structure.py    # Module import tests
python test_commands.py     # End-to-end command tests

# External access (for 메신저봇R)
ngrok http 8002

# Docker (uses port 8080, not 8002)
docker build -t kakao-bot . && docker run -p 8080:8080 kakao-bot

# Production (Digital Ocean - systemd)
sudo systemctl restart kakaobot
journalctl -u kakaobot -f
```

## Architecture

### fn.py Migration Pattern (CRITICAL)

The project is migrating from monolithic `fn.py` (~4,200 lines) to modular `handlers/`. **DO NOT DELETE `fn.py`** - it's still the source of truth for many functions including `web_summary`, `fortune`, `zodiac`.

**Override mechanism in `handlers/__init__.py`**:
```python
from fn import *              # 1st: Legacy functions (base layer)
from .ai_handler import *     # 2nd: Migrated handlers override fn.py
from .news_handler import *   # ...more overrides
```

Python's star-import uses last-wins semantics. When migrating a function:
1. Create handler in `handlers/{category}_handler.py`
2. Import in `handlers/__init__.py` **AFTER** `from fn import *` so it overrides
3. The old fn.py version becomes dead code but keep it as fallback

### Routing Logic (`core/router.py`)

`get_reply_msg(room, sender, msg)` uses lazy imports and cascading if/elif:

| Pattern | Handler | Notes |
|---------|---------|-------|
| `?질문` | `get_ai_answer()` | AI chat - strips `?` prefix, uses Gemini |
| `#검색어` | `naver_keyword()` | Naver keyword analysis |
| `/command` | Various handlers | Standard slash commands |
| URL in message | YouTube → `summarize()`, other → `web_summary()` | Auto-detection via regex |
| Greeting words | Auto-response | 안녕, 하이, 헬로, etc. |
| `han.gl` | Spam filter | Returns spam warning |

Admin-only commands (스케줄, 방관리, 오류모니터링) are gated by `config.is_admin_user(sender)`.

### Request Processing Pipeline (`main_improved.py`)

1. `POST /api/kakaotalk` receives `{room, sender, msg}`
2. Room whitelist check via `config.is_room_enabled(room)`
3. `get_reply_with_timeout()` applies per-command timeouts from `API_TIMEOUTS` dict
4. Result cached in `response_cache` with per-command TTL from `CACHE_TIMEOUTS` dict
5. `clean_message_for_kakao()` truncates to 1000 chars and replaces problematic emoji
6. Response as JSON with `ensure_ascii=True`

### Key Files

| File | Purpose |
|------|---------|
| `fn.py` | Legacy monolith - DO NOT DELETE |
| `main_improved.py` | FastAPI server, caching, timeouts, message cleaning |
| `core/router.py` | Message routing - `get_reply_msg()` |
| `command_manager.py` | Command registry (`ALL_COMMANDS` list), permissions, help text |
| `config.py` | Room whitelist, admin users, API keys (from `.env`) |
| `error_monitor.py` | Error tracking, auto-disables commands at >50% failure rate |
| `메신저r.js` | Android 메신저봇R script - client-side |

### Module Layout

- **`handlers/`**: ai, news, stock, media, game, utility, admin, schedule handlers
- **`services/`**: ai_service, http_service, db_service, web_scraping_service, schedule_service
- **`utils/`**: api_manager (API key rotation), debug_logger, text_utils
- **`movie_modules/`**: Movie ranking scrapers (playwright, selenium, HTTP fallbacks)
- **`data/`**: SQLite databases (`schedules.db`)

## Adding a New Command

1. **Register** in `command_manager.py` → `ALL_COMMANDS` list:
   ```python
   {"name": "/명령어", "description": "설명", "category": "카테고리",
    "handler": "function_name", "is_prefix": True, "admin_only": False}
   ```
2. **Implement** in `handlers/{category}_handler.py` — signature: `def handler(room, sender, msg)`
3. **Route** in `core/router.py` → add `elif` clause in `get_reply_msg()`
4. **Export** from `handlers/__init__.py` if new module

All handler functions take `(room: str, sender: str, msg: str)` and return `str` or `None`.

## Configuration

Copy `.env.example` to `.env` with API keys:
- **AI**: `GEMINI_API_KEY_{1-4}`, `CLAUDE_API_KEY`, `OPENAI_API_KEY`, `PERPLEXITY_API_KEY_{1-2}`
- **Data**: `YOUTUBE_API_KEY`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
- **Scraping**: `BRIGHT_DATA` proxy credentials

API key rotation uses numbered env vars (e.g., `GEMINI_API_KEY_1`, `_2`, `_3`, `_4`) via `utils/api_manager.py`.

Room whitelist and admin users are in `config.py` → `BOT_CONFIG`.

## Critical Constraints

| Constraint | Value | Why |
|-----------|-------|-----|
| Message length | 1000 chars | KakaoTalk limit, enforced in `clean_message_for_kakao()` |
| Default timeout | 4s | `API_TIMEOUTS['default']` in `main_improved.py` |
| URL summary timeout | 15s | Web scraping + LLM summarization |
| Cache size | 100 entries (LRU) | `MAX_CACHE_SIZE` in `main_improved.py` |
| Thread pool | 3 workers | `executor` in `main_improved.py` |
| Schedules per room | 20 | `MAX_SCHEDULES_PER_ROOM` in `schedule_service.py` |

Per-command timeouts and cache TTLs are defined in `API_TIMEOUTS` and `CACHE_TIMEOUTS` dicts in `main_improved.py`.

## Schedule System

`services/schedule_service.py` — APScheduler-based cron scheduling:
- Patterns: `매일`, `평일`, `주말`, `매주월`, `매월X일`
- Time: `HH:MM` or `오전/오후 X시 Y분`
- Storage: SQLite `data/schedules.db` + JSON `data/schedules.json`
- Delivery: `/api/poll` endpoint returns pending messages for 메신저봇R to send

## Error Monitoring

`error_monitor.py` tracks per-command failures. Commands exceeding 50% error rate are auto-disabled. Admin commands `/오류로그`, `/오류통계`, `/명령어활성화` for diagnostics.
