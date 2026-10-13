# Slice 1: Subscriptions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Telegram bot the Owner can use to register, list, and remove subreddit Subscriptions, with every `/add` validated against Reddit's live public feeds.

**Architecture:** A long-polling `python-telegram-bot` application over four thin layers — `config` (validated settings), `subreddit_name` (pure normalization), `store` (SQLite), `reddit` (async HTTP against public Atom feeds; the only module that talks to Reddit). Handlers live in a `Handlers` class holding its dependencies, so tests construct it with fakes and call the coroutines directly. No model, no scheduler, no fetching.

**Tech Stack:** Python 3.12, python-telegram-bot 21.x (async), `httpx` (already a transitive dependency of PTB, pinned here because `reddit.py` depends on it directly), stdlib `xml.etree.ElementTree` for Atom, Pydantic 2.x + pydantic-settings 2.x, stdlib `sqlite3`, pytest + pytest-asyncio.

> **Revised 2026-08-21.** This plan originally used PRAW against the Reddit API. That access was refused; see [ADR-0005](../../adr/0005-rss-is-the-permanent-source.md). Task 4 was rewritten and Tasks 1, 5 and 6 lost their credential and status-taxonomy assumptions. No code had been written against the API, so nothing was migrated.

**Reference:** [Design spec](../specs/2026-08-20-story-finder-design.md) · [CONTEXT.md](../../../CONTEXT.md) — the glossary is authoritative for naming.

## Global Constraints

- **All Owner-facing copy is Brazilian Portuguese.** Every reply string lives in `messages.py`; no literal user-facing text anywhere else. Logs stay in English.
- **The bot is never silent toward the Owner.** Every command produces a reply, including failures.
- **A non-owner receives no response at all.** Enforced by `filters.User`, so non-owner updates match no handler.
- **Subscriptions are hard-deleted.** There is no `active` flag; do not add one.
- **Pydantic at every boundary.** Domain objects and settings are Pydantic models; XML elements and `httpx` responses never escape `reddit.py`.
- **Subreddit names are stored lowercase and canonical.** Legal names are 3–21 characters of `[A-Za-z0-9_]`.
- **`reddit.py` owns request pacing.** Unauthenticated feeds 429 aggressively (observed at one request per 35s). No caller schedules Reddit requests or handles 429.
- Python floor: **3.12**. Handlers are async; `httpx.AsyncClient` is awaited directly — no thread offloading.

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Dependencies, pytest config |
| `src/story_finder/config.py` | `Settings` — env vars, validated at startup |
| `src/story_finder/subreddit_name.py` | Pure normalization and legality check |
| `src/story_finder/models.py` | `Subscription` domain model |
| `src/story_finder/store.py` | SQLite persistence |
| `src/story_finder/reddit.py` | `RedditClient`, `SubredditStatus` |
| `src/story_finder/messages.py` | Every pt-BR string |
| `src/story_finder/bot.py` | `Handlers`, owner filter, application wiring |
| `src/story_finder/__main__.py` | Entrypoint |
| `tests/` | Mirrors the above |

---

### Task 1: Project scaffolding and validated settings

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.env.example`, `src/story_finder/__init__.py`, `src/story_finder/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing
- Produces: `Settings` (pydantic-settings `BaseSettings`) with fields `telegram_bot_token: str`, `telegram_owner_id: int`, `reddit_user_agent: str`, `reddit_min_request_interval: float = 10.0`, `database_path: Path`. Constructed as `Settings()`.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "story-finder"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "python-telegram-bot>=21.0,<22",
    "httpx>=0.27,<1",
    "pydantic>=2.6,<3",
    "pydantic-settings>=2.2,<3",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/story_finder"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = ["contract: hits live Reddit feeds; excluded by default"]
addopts = "-m 'not contract'"
```

- [ ] **Step 2: Create `.gitignore` and `.env.example`**

`.gitignore`:
```
__pycache__/
*.py[cod]
.venv/
.env
*.db
.pytest_cache/
dist/
```

`.env.example`:
```
TELEGRAM_BOT_TOKEN=
TELEGRAM_OWNER_ID=
REDDIT_USER_AGENT=linux:story-finder:0.1.0 (by /u/yourname)
REDDIT_MIN_REQUEST_INTERVAL=10
DATABASE_PATH=./data/story_finder.db
```

- [ ] **Step 3: Write the failing test**

`tests/test_config.py`:
```python
import pytest
from pydantic import ValidationError

from story_finder.config import Settings


def _env(monkeypatch, **overrides):
    values = {
        "TELEGRAM_BOT_TOKEN": "token",
        "TELEGRAM_OWNER_ID": "12345",
        "REDDIT_USER_AGENT": "linux:story-finder:0.1.0 (by /u/test)",
        "DATABASE_PATH": "/tmp/sf.db",
    }
    values.update(overrides)
    for key in values:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        if value is not None:
            monkeypatch.setenv(key, value)


def test_settings_load_from_environment(monkeypatch):
    _env(monkeypatch)
    settings = Settings(_env_file=None)
    assert settings.telegram_owner_id == 12345
    assert settings.reddit_user_agent.startswith("linux:story-finder")


def test_missing_required_setting_is_a_validation_error(monkeypatch):
    _env(monkeypatch, TELEGRAM_BOT_TOKEN=None)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_owner_id_must_be_an_integer(monkeypatch):
    _env(monkeypatch, TELEGRAM_OWNER_ID="not-a-number")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'story_finder.config'`

- [ ] **Step 5: Write the implementation**

`src/story_finder/__init__.py` — empty file.

`src/story_finder/config.py`:
```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, validated at startup.

    A missing or malformed value raises immediately rather than surfacing
    as a mystery failure on the first command.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    telegram_owner_id: int
    reddit_user_agent: str
    reddit_min_request_interval: float = 10.0
    database_path: Path
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pip install -e ".[dev]" && pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/story_finder/__init__.py src/story_finder/config.py tests/test_config.py
git commit -m "feat: add project scaffolding and validated settings"
```

---

### Task 2: Subreddit name normalization

**Files:**
- Create: `src/story_finder/subreddit_name.py`
- Test: `tests/test_subreddit_name.py`

**Interfaces:**
- Consumes: nothing
- Produces: `normalize_subreddit(raw: str) -> str` returning the canonical lowercase name, raising `InvalidSubredditName(ValueError)` on anything illegal. Also exports `InvalidSubredditName`.

- [ ] **Step 1: Write the failing test**

`tests/test_subreddit_name.py`:
```python
import pytest

from story_finder.subreddit_name import InvalidSubredditName, normalize_subreddit


@pytest.mark.parametrize(
    "raw",
    [
        "python",
        "r/python",
        "/r/python",
        "R/Python",
        "https://reddit.com/r/python",
        "https://www.reddit.com/r/python/",
        "www.reddit.com/r/python",
        "  r/python  ",
    ],
)
def test_all_accepted_forms_normalize_to_the_same_name(raw):
    assert normalize_subreddit(raw) == "python"


def test_url_with_trailing_path_keeps_only_the_subreddit():
    assert normalize_subreddit(
        "https://www.reddit.com/r/rust/comments/abc123/some_title/"
    ) == "rust"


def test_underscores_and_digits_are_legal():
    assert normalize_subreddit("r/learn_python3") == "learn_python3"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "ab",                      # under 3 characters
        "a" * 22,                  # over 21 characters
        "py thon",                 # space
        "r/py-thon",               # hyphen is illegal
        "r/",
        "https://reddit.com/r/",
    ],
)
def test_illegal_input_is_rejected(raw):
    with pytest.raises(InvalidSubredditName):
        normalize_subreddit(raw)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_subreddit_name.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'story_finder.subreddit_name'`

- [ ] **Step 3: Write the implementation**

`src/story_finder/subreddit_name.py`:
```python
import re

_HOST = re.compile(r"^(?:https?://)?(?:[a-z0-9-]+\.)*reddit\.com", re.IGNORECASE)
_LEGAL = re.compile(r"^[A-Za-z0-9_]{3,21}$")


class InvalidSubredditName(ValueError):
    """Raised when input cannot be a subreddit name."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"not a legal subreddit name: {raw!r}")
        self.raw = raw


def normalize_subreddit(raw: str) -> str:
    """Return the canonical lowercase subreddit name.

    Accepts a bare name, an ``r/`` prefix with or without a leading slash,
    and a pasted reddit.com URL. Rejects anything that cannot be a legal
    subreddit name, so an illegal input never costs a network call.
    """
    text = _HOST.sub("", raw.strip()).strip("/")
    if text.lower().startswith("r/"):
        text = text[2:]
    text = text.strip("/").split("/")[0]
    if not _LEGAL.match(text):
        raise InvalidSubredditName(raw)
    return text.lower()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_subreddit_name.py -v`
Expected: 18 passed

- [ ] **Step 5: Commit**

```bash
git add src/story_finder/subreddit_name.py tests/test_subreddit_name.py
git commit -m "feat: normalize subreddit names from bare, r/, and URL forms"
```

---

### Task 3: SQLite store

**Files:**
- Create: `src/story_finder/models.py`, `src/story_finder/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `Subscription` — Pydantic model with `subreddit: str`, `added_at: datetime`
  - `Store(database_path: Path)` with `initialize() -> None`, `add_subscription(subreddit: str) -> bool` (False when already present), `list_subscriptions() -> list[Subscription]` (alphabetical), `remove_subscription(subreddit: str) -> bool` (False when absent), `close() -> None`

- [ ] **Step 1: Write the failing test**

`tests/test_store.py`:
```python
import pytest

from story_finder.store import Store


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "test.db")
    s.initialize()
    yield s
    s.close()


def test_add_then_list_returns_the_subscription(store):
    assert store.add_subscription("python") is True
    subs = store.list_subscriptions()
    assert [s.subreddit for s in subs] == ["python"]
    assert subs[0].added_at is not None


def test_adding_a_duplicate_returns_false_and_does_not_duplicate(store):
    assert store.add_subscription("python") is True
    assert store.add_subscription("python") is False
    assert len(store.list_subscriptions()) == 1


def test_list_is_alphabetical(store):
    for name in ["rust", "python", "golang"]:
        store.add_subscription(name)
    assert [s.subreddit for s in store.list_subscriptions()] == [
        "golang",
        "python",
        "rust",
    ]


def test_remove_deletes_the_row_and_reports_true(store):
    store.add_subscription("python")
    assert store.remove_subscription("python") is True
    assert store.list_subscriptions() == []


def test_removing_something_absent_reports_false(store):
    assert store.remove_subscription("python") is False


def test_initialize_is_idempotent(tmp_path):
    path = tmp_path / "test.db"
    first = Store(path)
    first.initialize()
    first.add_subscription("python")
    first.close()

    second = Store(path)
    second.initialize()
    assert [s.subreddit for s in second.list_subscriptions()] == ["python"]
    second.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'story_finder.store'`

- [ ] **Step 3: Write the domain model**

`src/story_finder/models.py`:
```python
from datetime import datetime

from pydantic import BaseModel


class Subscription(BaseModel):
    """A subreddit the Owner tracks."""

    subreddit: str
    added_at: datetime
```

- [ ] **Step 4: Write the store**

`src/story_finder/store.py`:
```python
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from story_finder.models import Subscription

_SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    subreddit TEXT PRIMARY KEY,
    added_at  TEXT NOT NULL
);
"""


class Store:
    """SQLite persistence. Subscriptions are hard-deleted; there is no active flag."""

    def __init__(self, database_path: Path) -> None:
        self._path = Path(database_path)
        self._connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    @property
    def _db(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("Store.initialize() was never called")
        return self._connection

    def add_subscription(self, subreddit: str) -> bool:
        try:
            self._db.execute(
                "INSERT INTO subscriptions (subreddit, added_at) VALUES (?, ?)",
                (subreddit, datetime.now(timezone.utc).isoformat()),
            )
        except sqlite3.IntegrityError:
            return False
        self._db.commit()
        return True

    def list_subscriptions(self) -> list[Subscription]:
        rows = self._db.execute(
            "SELECT subreddit, added_at FROM subscriptions ORDER BY subreddit"
        ).fetchall()
        return [
            Subscription(subreddit=row["subreddit"], added_at=row["added_at"])
            for row in rows
        ]

    def remove_subscription(self, subreddit: str) -> bool:
        cursor = self._db.execute(
            "DELETE FROM subscriptions WHERE subreddit = ?", (subreddit,)
        )
        self._db.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_store.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add src/story_finder/models.py src/story_finder/store.py tests/test_store.py
git commit -m "feat: add SQLite store for subscriptions"
```

---

### Task 4: Reddit feed client and status taxonomy

**Files:**
- Create: `src/story_finder/reddit.py`
- Test: `tests/test_reddit.py`, `tests/test_reddit_contract.py`

**Interfaces:**
- Consumes: `Settings` (Task 1)
- Produces:
  - `SubredditStatus` — `StrEnum` with members `OK`, `NOT_FOUND`, `FORBIDDEN`, `RATE_LIMITED`, `UNAVAILABLE`
  - `RedditClient(settings, client=None, sleep=asyncio.sleep, clock=time.monotonic)` with `async def check_subreddit(name: str) -> SubredditStatus` and `async def aclose() -> None`
  - `classify_status(code: int) -> SubredditStatus` — pure, unit-testable

**Why this shape.** Reddit's API access was refused ([ADR-0005](../../adr/0005-rss-is-the-permanent-source.md)), so validation is an HTTP GET of `https://www.reddit.com/r/<name>/top/.rss?t=week&limit=100` and the only signal available is the status code. Probed live on 2026-08-21:

| Observed | Status | Notes |
|---|---|---|
| `r/python`, `r/UnresolvedMysteries` | 200 | 12 and 16 `<entry>` elements respectively |
| `r/thisdefinitelydoesnotexist99z` | 404 | body is a **well-formed empty Atom feed**, not an error page |
| `r/CenturyClub` (private) | 403 | body title: `reddit.com: forbidden` |
| `r/TheRedPill` (quarantined) | 403 | identical body shape |
| `r/MorbidReality` (quarantined) | 403 | identical body shape |
| burst traffic | 429 | empty body; seen even at one request per 35s |

Two consequences the implementation must respect:

1. **Never parse the body to decide reachability.** A 404 returns valid Atom. The status code is the whole taxonomy.
2. **Private, banned and quarantined are indistinguishable.** They collapse to `FORBIDDEN`, and Task 5's message names all three possibilities rather than guessing one.

- [ ] **Step 1: Write the failing test**

`tests/test_reddit.py`:
```python
import httpx
import pytest

from story_finder.config import Settings
from story_finder.reddit import RedditClient, SubredditStatus, classify_status


def test_200_is_ok():
    assert classify_status(200) is SubredditStatus.OK


def test_404_means_the_subreddit_does_not_exist():
    assert classify_status(404) is SubredditStatus.NOT_FOUND


def test_403_is_forbidden_without_guessing_why():
    # Private, banned and quarantined all return 403 with an identical body.
    assert classify_status(403) is SubredditStatus.FORBIDDEN


def test_429_is_rate_limited():
    assert classify_status(429) is SubredditStatus.RATE_LIMITED


def test_server_error_is_unavailable():
    assert classify_status(503) is SubredditStatus.UNAVAILABLE


def _settings(**overrides):
    values = {
        "telegram_bot_token": "t",
        "telegram_owner_id": 1,
        "reddit_user_agent": "linux:story-finder:0.1.0 (by /u/test)",
        "reddit_min_request_interval": 0.0,
        "database_path": "/tmp/sf.db",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def _client(handler, **overrides):
    """A RedditClient wired to a mock transport and a clock that never really sleeps."""
    elapsed = [0.0]

    async def sleep(seconds):
        elapsed[0] += seconds

    transport = httpx.MockTransport(handler)
    client = RedditClient(
        _settings(**overrides),
        client=httpx.AsyncClient(transport=transport),
        sleep=sleep,
        clock=lambda: elapsed[0],
    )
    return client, elapsed


async def test_readable_subreddit_is_ok():
    client, _ = _client(lambda request: httpx.Response(200, text="<feed/>"))
    assert await client.check_subreddit("python") is SubredditStatus.OK
    await client.aclose()


async def test_the_user_agent_is_sent():
    seen = {}

    def handler(request):
        seen["ua"] = request.headers["user-agent"]
        return httpx.Response(200, text="<feed/>")

    client, _ = _client(handler)
    await client.check_subreddit("python")
    assert seen["ua"].startswith("linux:story-finder")
    await client.aclose()


async def test_a_404_is_not_found_even_though_the_body_is_valid_atom():
    body = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"/>'
    client, _ = _client(lambda request: httpx.Response(404, text=body))
    assert await client.check_subreddit("nope") is SubredditStatus.NOT_FOUND
    await client.aclose()


async def test_a_transient_429_is_retried_and_succeeds():
    codes = [429, 429, 200]

    def handler(request):
        return httpx.Response(codes.pop(0), text="<feed/>")

    client, _ = _client(handler)
    assert await client.check_subreddit("python") is SubredditStatus.OK
    assert not codes  # all three responses consumed
    await client.aclose()


async def test_a_persistent_429_surfaces_as_rate_limited():
    client, _ = _client(lambda request: httpx.Response(429))
    assert await client.check_subreddit("python") is SubredditStatus.RATE_LIMITED
    await client.aclose()


async def test_backoff_between_retries_grows():
    client, elapsed = _client(lambda request: httpx.Response(429))
    await client.check_subreddit("python")
    # 2 + 4 + 8 = 14s of backoff across three retries.
    assert elapsed[0] >= 14.0
    await client.aclose()


async def test_requests_are_paced_by_the_minimum_interval():
    client, elapsed = _client(
        lambda request: httpx.Response(200, text="<feed/>"),
        reddit_min_request_interval=10.0,
    )
    await client.check_subreddit("python")
    first = elapsed[0]
    await client.check_subreddit("ruby")
    assert elapsed[0] - first >= 10.0
    await client.aclose()


async def test_a_network_error_is_unavailable():
    def handler(request):
        raise httpx.ConnectError("boom")

    client, _ = _client(handler)
    assert await client.check_subreddit("python") is SubredditStatus.UNAVAILABLE
    await client.aclose()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reddit.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'story_finder.reddit'`

- [ ] **Step 3: Write the implementation**

`src/story_finder/reddit.py`:
```python
import asyncio
import logging
import time
from collections.abc import Callable
from enum import StrEnum

import httpx

from story_finder.config import Settings

logger = logging.getLogger(__name__)

FEED_URL = "https://www.reddit.com/r/{name}/top/.rss"
MAX_RATE_LIMIT_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2.0


class SubredditStatus(StrEnum):
    OK = "ok"
    NOT_FOUND = "not_found"
    # Private, banned and quarantined are indistinguishable over RSS: all three
    # return 403 with the same body. Do not split this without new evidence.
    FORBIDDEN = "forbidden"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"


def classify_status(code: int) -> SubredditStatus:
    """Map an HTTP status onto something the Owner can be told.

    The status code is the entire signal: a 404 comes back as a well-formed but
    empty Atom feed, so the body cannot be trusted to indicate failure.
    """
    match code:
        case 200:
            return SubredditStatus.OK
        case 404:
            return SubredditStatus.NOT_FOUND
        case 403:
            return SubredditStatus.FORBIDDEN
        case 429:
            return SubredditStatus.RATE_LIMITED
        case _:
            return SubredditStatus.UNAVAILABLE


class RedditClient:
    """The only module that talks to Reddit.

    Owns request pacing and 429 backoff so no caller has to. Unauthenticated
    feeds rate-limit hard — 429s were observed at one request per 35 seconds —
    and a Digest's five weekly requests are nowhere near the problem; a burst of
    Owner-triggered /add calls is.

    `sleep` and `clock` are injected so pacing is testable without real time.
    """

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        sleep: Callable = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._headers = {"User-Agent": settings.reddit_user_agent}
        self._min_interval = settings.reddit_min_request_interval
        self._client = client or httpx.AsyncClient(timeout=15.0)
        self._sleep = sleep
        self._clock = clock
        self._lock = asyncio.Lock()
        self._last_request_at: float | None = None

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _paced_get(self, url: str, params: dict) -> int:
        """One request, never sooner than the minimum interval. Returns a status."""
        async with self._lock:
            if self._last_request_at is not None:
                wait = self._min_interval - (self._clock() - self._last_request_at)
                if wait > 0:
                    await self._sleep(wait)
            try:
                response = await self._client.get(
                    url, params=params, headers=self._headers
                )
                return response.status_code
            finally:
                self._last_request_at = self._clock()

    async def check_subreddit(self, name: str) -> SubredditStatus:
        url = FEED_URL.format(name=name)
        params = {"t": "week", "limit": "100"}
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            try:
                status = classify_status(await self._paced_get(url, params))
            except httpx.HTTPError as exc:
                logger.info("subreddit %s check failed: %s", name, exc)
                return SubredditStatus.UNAVAILABLE

            if status is not SubredditStatus.RATE_LIMITED:
                if status is not SubredditStatus.OK:
                    logger.info("subreddit %s check: %s", name, status)
                return status

            if attempt < MAX_RATE_LIMIT_RETRIES:
                logger.info("rate limited on %s, backing off %.0fs", name, backoff)
                await self._sleep(backoff)
                backoff *= 2

        logger.warning("subreddit %s still rate limited after retries", name)
        return SubredditStatus.RATE_LIMITED
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_reddit.py -v`
Expected: 13 passed

- [ ] **Step 5: Write the contract test**

`tests/test_reddit_contract.py`:
```python
import pytest

from story_finder.config import Settings
from story_finder.reddit import RedditClient, SubredditStatus

pytestmark = pytest.mark.contract


@pytest.fixture(scope="module")
async def client():
    # Real settings, real pacing — this test is deliberately slow.
    c = RedditClient(Settings())
    yield c
    await c.aclose()


async def test_public_subreddit_is_ok(client):
    assert await client.check_subreddit("python") is SubredditStatus.OK


async def test_nonexistent_subreddit_is_not_found(client):
    assert (
        await client.check_subreddit("thisdefinitelydoesnotexist99z")
        is SubredditStatus.NOT_FOUND
    )


async def test_quarantined_subreddit_is_forbidden(client):
    assert await client.check_subreddit("MorbidReality") is SubredditStatus.FORBIDDEN
```

- [ ] **Step 6: Run the contract test explicitly**

Run: `pytest tests/test_reddit_contract.py -v -m contract`
Expected: 3 passed, taking at least 20 seconds because of pacing. Needs no credentials — only network.

Then confirm the default suite still skips it:
Run: `pytest -v`
Expected: contract tests deselected.

> If `test_quarantined_subreddit_is_forbidden` starts failing with `OK`, Reddit has opened quarantined feeds to anonymous readers and issue #3's answer has changed. Do not "fix" the test — reopen #3.

- [ ] **Step 7: Probe NSFW reachability and record the finding (issue #3)**

This is the scope-determining question in the slice, and it is now larger than it was: with API credentials off the table there is no fallback if NSFW-flagged communities are unreadable. `r/MorbidReality` — one of the five subreddits this bot exists for — already returns 403.

Probe each of the five intended subreddits, spacing requests generously so rate limiting does not masquerade as a refusal:

```bash
UA="linux:story-finder:0.1.0 (by /u/yourname)"
for s in UnresolvedMysteries TrueCrime MorbidReality Paranormal LetsNotMeet; do
  printf '%s -> ' "$s"
  curl -sS -o /dev/null -w '%{http_code}\n' -A "$UA" \
    "https://www.reddit.com/r/$s/top/.rss?t=week&limit=100"
  sleep 45
done
```

Record the result in the spec's Slice 1 section, replacing the sentence that says NSFW reachability is unsettled. State plainly which of the five are readable. If a material share are not, that is a product-scope finding, not a code branch — say so in the issue rather than papering over it.

- [ ] **Step 8: Commit**

```bash
git add src/story_finder/reddit.py tests/test_reddit.py tests/test_reddit_contract.py docs/superpowers/specs/2026-08-20-story-finder-design.md
git commit -m "feat: add Reddit feed client with status classification and pacing"
```

---

### Task 5: pt-BR message catalog

**Files:**
- Create: `src/story_finder/messages.py`
- Test: `tests/test_messages.py`

**Interfaces:**
- Consumes: `SubredditStatus` (Task 4)
- Produces: `START`, `ADDED(name)`, `ALREADY_SUBSCRIBED(name)`, `REMOVED(name)`, `NOT_SUBSCRIBED(name)`, `EMPTY_LIST`, `LIST_HEADER`, `INVALID_NAME(raw)`, `UNEXPECTED_ERROR`, and `for_status(status: SubredditStatus, name: str) -> str`.

- [ ] **Step 1: Write the failing test**

`tests/test_messages.py`:
```python
import pytest

from story_finder import messages
from story_finder.reddit import SubredditStatus


@pytest.mark.parametrize("status", list(SubredditStatus))
def test_every_status_has_a_message(status):
    text = messages.for_status(status, "python")
    assert isinstance(text, str) and text.strip()


def test_failure_messages_are_distinct_per_status():
    failures = [s for s in SubredditStatus if s is not SubredditStatus.OK]
    rendered = {messages.for_status(s, "python") for s in failures}
    assert len(rendered) == len(failures)


def test_messages_name_the_subreddit():
    assert "python" in messages.for_status(SubredditStatus.NOT_FOUND, "python")
    assert "python" in messages.ADDED("python")


def test_copy_is_portuguese_not_english():
    # A cheap guard against an English string slipping into Owner-facing copy.
    english_giveaways = ["not found", "error", "subscribed", "removed"]
    text = " ".join(
        [messages.START, messages.EMPTY_LIST, messages.UNEXPECTED_ERROR]
    ).lower()
    assert not any(word in text for word in english_giveaways)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_messages.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'story_finder.messages'`

- [ ] **Step 3: Write the implementation**

`src/story_finder/messages.py`:
```python
"""Every Owner-facing string. No user-facing text lives anywhere else."""

from story_finder.reddit import SubredditStatus

START = (
    "Olá! Eu acompanho comunidades do Reddit para você.\n\n"
    "Use /add <comunidade> para começar a acompanhar uma, "
    "/list para ver as que você já acompanha e "
    "/remove <comunidade> para parar de acompanhar."
)

EMPTY_LIST = "Você ainda não acompanha nenhuma comunidade. Use /add para adicionar a primeira."

LIST_HEADER = "Comunidades que você acompanha:"

UNEXPECTED_ERROR = "Algo deu errado por aqui. Tente novamente em instantes."

USAGE_ADD = "Envie assim: /add <comunidade>. Por exemplo: /add python"

USAGE_REMOVE = "Envie assim: /remove <comunidade>. Por exemplo: /remove python"


def ADDED(name: str) -> str:
    return f"Pronto! Agora acompanho r/{name}."


def ALREADY_SUBSCRIBED(name: str) -> str:
    return f"Você já acompanha r/{name}."


def REMOVED(name: str) -> str:
    return f"Parei de acompanhar r/{name}."


def NOT_SUBSCRIBED(name: str) -> str:
    return f"Você não acompanha r/{name}, então não há o que remover."


def INVALID_NAME(raw: str) -> str:
    return (
        f"{raw!r} não parece o nome de uma comunidade. "
        "Use algo como python, r/python ou o link da comunidade."
    )


_STATUS_MESSAGES = {
    SubredditStatus.OK: "r/{name} está acessível.",
    SubredditStatus.NOT_FOUND: "Não encontrei a comunidade r/{name}.",
    # Private, banned and quarantined are indistinguishable over RSS — all three
    # return 403 with an identical body — so this message names all three rather
    # than confidently asserting the wrong one.
    SubredditStatus.FORBIDDEN: (
        "Não consigo ler r/{name}. Ela pode ser privada, estar em quarentena "
        "ou ter sido banida — o Reddit não informa qual."
    ),
    SubredditStatus.RATE_LIMITED: (
        "O Reddit está limitando meus acessos agora. Tente de novo em um minuto."
    ),
    SubredditStatus.UNAVAILABLE: (
        "Não consegui falar com o Reddit agora. Tente novamente em instantes."
    ),
}


def for_status(status: SubredditStatus, name: str) -> str:
    return _STATUS_MESSAGES[status].format(name=name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_messages.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/story_finder/messages.py tests/test_messages.py
git commit -m "feat: add pt-BR message catalog"
```

---

### Task 6: Command handlers

**Files:**
- Create: `src/story_finder/bot.py`
- Test: `tests/test_handlers.py`

**Interfaces:**
- Consumes: `Store` (Task 3), `RedditClient` and `SubredditStatus` (Task 4), `messages` (Task 5), `normalize_subreddit` and `InvalidSubredditName` (Task 2)
- Produces: `Handlers(store, reddit)` with `async start`, `async add`, `async list_`, `async remove`, each taking `(update, context)`. Also `build_application(settings, store, reddit)` returning a configured `telegram.ext.Application`.

- [ ] **Step 1: Write the failing test**

`tests/test_handlers.py`:
```python
import pytest

from story_finder import messages
from story_finder.bot import Handlers
from story_finder.reddit import SubredditStatus
from story_finder.store import Store


class FakeReddit:
    def __init__(self, status=SubredditStatus.OK):
        self.status = status
        self.checked: list[str] = []

    async def check_subreddit(self, name: str) -> SubredditStatus:
        self.checked.append(name)
        return self.status


class FakeMessage:
    def __init__(self):
        self.replies: list[str] = []

    async def reply_text(self, text: str, **kwargs) -> None:
        self.replies.append(text)


class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()


class FakeContext:
    def __init__(self, args=None):
        self.args = args or []


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "test.db")
    s.initialize()
    yield s
    s.close()


async def test_start_replies_in_portuguese(store):
    handlers = Handlers(store, FakeReddit())
    update, context = FakeUpdate(), FakeContext()
    await handlers.start(update, context)
    assert update.message.replies == [messages.START]


async def test_add_normalizes_validates_and_persists(store):
    reddit = FakeReddit(SubredditStatus.OK)
    handlers = Handlers(store, reddit)
    update, context = FakeUpdate(), FakeContext(["/r/Python/"])
    await handlers.add(update, context)

    assert reddit.checked == ["python"]
    assert update.message.replies == [messages.ADDED("python")]
    assert [s.subreddit for s in store.list_subscriptions()] == ["python"]


async def test_add_rejects_an_illegal_name_without_calling_reddit(store):
    reddit = FakeReddit()
    handlers = Handlers(store, reddit)
    update, context = FakeUpdate(), FakeContext(["py thon"])
    await handlers.add(update, context)

    assert reddit.checked == []
    assert update.message.replies == [messages.INVALID_NAME("py thon")]
    assert store.list_subscriptions() == []


@pytest.mark.parametrize(
    "status",
    [
        SubredditStatus.NOT_FOUND,
        SubredditStatus.FORBIDDEN,
        SubredditStatus.RATE_LIMITED,
        SubredditStatus.UNAVAILABLE,
    ],
)
async def test_add_reports_each_failure_and_persists_nothing(store, status):
    handlers = Handlers(store, FakeReddit(status))
    update, context = FakeUpdate(), FakeContext(["python"])
    await handlers.add(update, context)

    assert update.message.replies == [messages.for_status(status, "python")]
    assert store.list_subscriptions() == []


async def test_add_reports_a_duplicate(store):
    handlers = Handlers(store, FakeReddit(SubredditStatus.OK))
    context = FakeContext(["python"])
    await handlers.add(FakeUpdate(), context)

    update = FakeUpdate()
    await handlers.add(update, FakeContext(["python"]))
    assert update.message.replies == [messages.ALREADY_SUBSCRIBED("python")]


async def test_add_without_an_argument_explains_usage(store):
    handlers = Handlers(store, FakeReddit())
    update, context = FakeUpdate(), FakeContext([])
    await handlers.add(update, context)
    assert update.message.replies == [messages.USAGE_ADD]


async def test_list_when_empty_says_so(store):
    handlers = Handlers(store, FakeReddit())
    update, context = FakeUpdate(), FakeContext()
    await handlers.list_(update, context)
    assert update.message.replies == [messages.EMPTY_LIST]


async def test_list_shows_each_subscription(store):
    store.add_subscription("python")
    store.add_subscription("rust")
    handlers = Handlers(store, FakeReddit())
    update, context = FakeUpdate(), FakeContext()
    await handlers.list_(update, context)

    reply = update.message.replies[0]
    assert messages.LIST_HEADER in reply
    assert "r/python" in reply and "r/rust" in reply


async def test_remove_deletes_and_confirms(store):
    store.add_subscription("python")
    handlers = Handlers(store, FakeReddit())
    update, context = FakeUpdate(), FakeContext(["r/python"])
    await handlers.remove(update, context)

    assert update.message.replies == [messages.REMOVED("python")]
    assert store.list_subscriptions() == []


async def test_remove_of_an_absent_subscription_says_so(store):
    handlers = Handlers(store, FakeReddit())
    update, context = FakeUpdate(), FakeContext(["python"])
    await handlers.remove(update, context)
    assert update.message.replies == [messages.NOT_SUBSCRIBED("python")]


async def test_remove_does_not_call_reddit(store):
    store.add_subscription("python")
    reddit = FakeReddit()
    handlers = Handlers(store, reddit)
    await handlers.remove(FakeUpdate(), FakeContext(["python"]))
    assert reddit.checked == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_handlers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'story_finder.bot'`

- [ ] **Step 3: Write the implementation**

`src/story_finder/bot.py`:
```python
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from story_finder import messages
from story_finder.config import Settings
from story_finder.reddit import RedditClient, SubredditStatus
from story_finder.store import Store
from story_finder.subreddit_name import InvalidSubredditName, normalize_subreddit

logger = logging.getLogger(__name__)


class Handlers:
    """Telegram command handlers.

    Knows nothing about Reddit's or SQLite's internals — it calls the layers
    below and formats replies. Every path replies to the Owner; none is silent.
    """

    def __init__(self, store: Store, reddit: RedditClient) -> None:
        self._store = store
        self._reddit = reddit

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(messages.START)

    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text(messages.USAGE_ADD)
            return

        raw = context.args[0]
        try:
            name = normalize_subreddit(raw)
        except InvalidSubredditName:
            await update.message.reply_text(messages.INVALID_NAME(raw))
            return

        status = await self._reddit.check_subreddit(name)
        if status is not SubredditStatus.OK:
            await update.message.reply_text(messages.for_status(status, name))
            return

        if self._store.add_subscription(name):
            await update.message.reply_text(messages.ADDED(name))
        else:
            await update.message.reply_text(messages.ALREADY_SUBSCRIBED(name))

    async def list_(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        subscriptions = self._store.list_subscriptions()
        if not subscriptions:
            await update.message.reply_text(messages.EMPTY_LIST)
            return

        lines = [messages.LIST_HEADER] + [
            f"• r/{s.subreddit}" for s in subscriptions
        ]
        await update.message.reply_text("\n".join(lines))

    async def remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text(messages.USAGE_REMOVE)
            return

        raw = context.args[0]
        try:
            name = normalize_subreddit(raw)
        except InvalidSubredditName:
            await update.message.reply_text(messages.INVALID_NAME(raw))
            return

        if self._store.remove_subscription(name):
            await update.message.reply_text(messages.REMOVED(name))
        else:
            await update.message.reply_text(messages.NOT_SUBSCRIBED(name))


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log in English, reply in pt-BR. A stack trace never reaches the Owner."""
    logger.exception("unhandled error while processing update", exc_info=context.error)
    if isinstance(update, Update) and update.message is not None:
        await update.message.reply_text(messages.UNEXPECTED_ERROR)


def build_application(
    settings: Settings, store: Store, reddit: RedditClient
) -> Application:
    """Wire handlers behind an Owner-only filter.

    Non-owner updates match no handler and therefore receive no response at all —
    the bot does not advertise itself to strangers.
    """
    application = Application.builder().token(settings.telegram_bot_token).build()
    handlers = Handlers(store, reddit)
    owner_only = filters.User(user_id=settings.telegram_owner_id)

    application.add_handler(CommandHandler("start", handlers.start, filters=owner_only))
    application.add_handler(CommandHandler("add", handlers.add, filters=owner_only))
    application.add_handler(CommandHandler("list", handlers.list_, filters=owner_only))
    application.add_handler(
        CommandHandler("remove", handlers.remove, filters=owner_only)
    )
    application.add_error_handler(_on_error)
    return application
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_handlers.py -v`
Expected: 15 passed

- [ ] **Step 5: Run the whole suite**

Run: `pytest -v`
Expected: all pass, contract tests deselected

- [ ] **Step 6: Commit**

```bash
git add src/story_finder/bot.py tests/test_handlers.py
git commit -m "feat: add owner-locked subscription commands"
```

---

### Task 7: Entrypoint and container packaging

**Files:**
- Create: `src/story_finder/__main__.py`, `Dockerfile`, `docker-compose.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: `build_application` (Task 6), `Settings` (Task 1), `Store` (Task 3), `RedditClient` (Task 4)
- Produces: `python -m story_finder` starts the bot; `docker compose up` runs it in a container.

- [ ] **Step 1: Write the entrypoint**

`src/story_finder/__main__.py`:
```python
import logging

from story_finder.bot import build_application
from story_finder.config import Settings
from story_finder.reddit import RedditClient
from story_finder.store import Store


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Settings validation runs first: a bad config fails here, not on first command.
    settings = Settings()

    store = Store(settings.database_path)
    store.initialize()
    reddit = RedditClient(settings)

    application = build_application(settings, store, reddit)
    logging.getLogger(__name__).info("starting long-polling")
    application.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it starts and responds**

With a real `.env` in place:

Run: `python -m story_finder`
Expected: logs `starting long-polling` and stays running.

In Telegram, send `/start`, then `/add r/python`, `/list`, `/remove python`. Expected: pt-BR replies at each step, and `/add` persists across a restart.

- [ ] **Step 3: Write the Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# SQLite lives on a mounted volume so moving hosts is copying one file.
VOLUME ["/data"]
ENV DATABASE_PATH=/data/story_finder.db

CMD ["python", "-m", "story_finder"]
```

- [ ] **Step 4: Write the compose file**

`docker-compose.yml`:
```yaml
services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_PATH: /data/story_finder.db
    volumes:
      - ./data:/data
```

- [ ] **Step 5: Verify the container runs**

Run: `docker compose up --build`
Expected: same startup log; the same Telegram commands work; `./data/story_finder.db` appears on the host and survives `docker compose down && docker compose up`.

- [ ] **Step 6: Document setup in the README**

Add a "Running locally" section covering: registering a script app at
`reddit.com/prefs/apps` and a bot with `@BotFather`, copying `.env.example` to
`.env`, finding your Telegram user ID, and `docker compose up --build`. State that
the bot answers only that user ID and ignores everyone else.

- [ ] **Step 7: Commit**

```bash
git add src/story_finder/__main__.py Dockerfile docker-compose.yml README.md
git commit -m "feat: add entrypoint and container packaging"
```

---

## Done when

- `pytest` passes with contract tests deselected; `pytest -m contract` passes against live Reddit.
- `/start`, `/add`, `/list`, `/remove` all reply in pt-BR, including every failure.
- A second Telegram account sending `/start` receives nothing at all.
- Subscriptions survive `docker compose down && docker compose up`.
- The NSFW probe from Task 4 Step 7 is recorded in the spec.
