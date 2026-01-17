# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STORIUM Bot - A KakaoTalk integrated bot system that connects via 메신저봇R (Messenger Bot R) to provide 31+ commands across AI chat, real-time information, search, finance, entertainment, and utilities.

**Architecture:** Modular monolith transitioning to service-oriented architecture. The core message flow is: KakaoTalk → 메신저봇R → FastAPI Server → Command Processing → Response.

## Running the Server

```bash
# Development
python main_improved.py

# With Docker
docker build -t kakao-bot .
docker run -p 8080:8080 kakao-bot

# External access (for 메신저봇R connection)
ngrok http 8000
```

## Dependencies

```bash
pip install -r requirements.txt
playwright install chromium  # For movie rankings
```

## Code Architecture

### Current Structure (Migration in Progress)

The project is migrating from a monolithic `fn.py` (4,200+ lines) to a modular structure:

```
kakaoBot-main/
├── main_improved.py       # FastAPI server (entry point)
├── config.py              # Central configuration management
├── command_manager.py     # Command registry & metadata
├── fn.py                  # Legacy command processing (DO NOT DELETE - being phased out)
│
├── core/                  # Core routing & messaging
│   ├── router.py          # Message routing - delegates to handlers
│   └── message_handler.py
│
├── handlers/              # Feature-specific handlers (7 modules)
│   ├── ai_handler.py      # AI conversation (GPT/Claude/Gemini)
│   ├── news_handler.py    # News search & aggregation
│   ├── stock_handler.py   # Stock/finance data
│   ├── media_handler.py   # YouTube, movies, entertainment
│   ├── game_handler.py    # Games (LOL lottery, etc.)
│   ├── utility_handler.py # Weather, maps, calories, etc.
│   └── admin_handler.py   # Admin-only commands
│
├── services/              # Business logic layer
│   ├── ai_service.py      # AI API integration
│   ├── http_service.py    # HTTP request management
│   ├── db_service.py      # Database operations
│   └── web_scraping_service.py
│
├── utils/                 # Shared utilities
│   ├── api_manager.py
│   └── debug_logger.py
│
└── movie_modules/         # Movie ranking scrapers (Playwright/Selenium/Direct)
```

### Key Files - Do Not Modify Without Understanding

| File | Purpose | Lines |
|------|---------|-------|
| `fn.py` | Legacy command processing - being migrated to handlers | ~4,200 |
| `main_improved.py` | FastAPI server with timeout & caching | ~920 |
| `command_manager.py` | Command registry, permissions, metadata | ~614 |
| `config.py` | Central configuration, API keys, room access | ~185 |
| `core/router.py` | Message routing to appropriate handlers | ~270 |

### Message Flow

1. **Request**: KakaoTalk → 메신저봇R → POST `/api/kakaotalk`
2. **Routing**: `core/router.py:get_reply_msg()` parses command
3. **Handler**: Delegates to appropriate handler function
4. **Service**: Handler calls service layer for business logic
5. **Response**: Formatted and cached response sent back

## Adding Commands

1. **Register** in `command_manager.py` → `ALL_COMMANDS` list
2. **Implement** in appropriate handler (`handlers/*.py`)
3. **Route** in `core/router.py` → add elif clause
4. **Test** via `/테스트` or actual 카카오톡 message

## Configuration

- **Room Access Control**: `config.py` → `BOT_CONFIG["ALLOWED_ROOMS"]`
- **Admin Users**: `config.py` → `ADMIN_USERS`
- **API Keys**: Stored in `.env` (not committed), loaded via `python-dotenv`
- **ngrok URL**: Auto-detected from localhost:4040 API

## Response Cache Timeouts (defined in main_improved.py)

- **24h**: `/영화순위`, `/로또결과`
- **5min**: `/환율`, `/금값`
- **3min**: `/코인`
- **1min**: `/주식`
- **No cache**: `?` (AI chat)

## Critical Timeouts

- **Commands**: 4 seconds
- **AI Chat**: 8 seconds (currently disabled)
- **Message limit**: 1000 characters

## Migration Status (Phases 1-3 Complete, Phase 4 In Progress)

- ✅ Phase 1: Handler separation (`handlers/` directory)
- ✅ Phase 2: Service layer implementation (`services/` directory)
- ✅ Phase 3: Core module improvements (`core/` directory)
- 🔄 Phase 4: Progressive migration from `fn.py`

See `MIGRATION_PLAN.md` for details.

## Testing

```bash
python test_services.py   # Service layer tests
python test_structure.py  # Module import tests
```

## Deployment

- **Dockerfile** uses `python:3.11-slim`
- **DigitalOcean App Platform** configured for auto-deploy
- **Port**: 8002 (configurable)
- **Endpoint**: `/api/kakaotalk`
