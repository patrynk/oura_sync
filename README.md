# Oura Ring Data Sync

A Python service for syncing Oura Ring data to a PostgreSQL database with secure OAuth2 authentication. Automatically handles token refresh, rate limiting, and provides comprehensive access to all Oura API v2 endpoints.

## Features

- **Secure OAuth2 Authentication** - Uses `requests-oauthlib` for proper OAuth2 flows with CSRF protection
- **Automatic Token Management** - Handles token refresh automatically, including Oura's single-use refresh tokens
- **Comprehensive API Coverage** - Supports all Oura API v2 data types (daily summaries, time-series, sessions, etc.)
- **Robust Error Handling** - Automatic retries with exponential backoff and rate limit handling
- **Database Models** - SQLAlchemy models for all data types with timestamp tracking
- **Production Ready** - Proper logging, timezone handling, and configurable via environment variables

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Data Types](#data-types)
- [Database Schema](#database-schema)
- [Scheduling](#scheduling)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- Oura Ring with API access
- Oura Developer Application ([create one here](https://cloud.ouraring.com/oauth/applications))

## Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd oura_sync
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

## Configuration

1. **Create your Oura Developer Application**

Visit [https://cloud.ouraring.com/oauth/applications](https://cloud.ouraring.com/oauth/applications) and create a new application:
- **Redirect URI**: `http://localhost:8000/callback`
- Note your **Client ID** and **Client Secret**

2. **Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Oura API OAuth2 Settings
OURA_CLIENT_ID=your_client_id_here
OURA_CLIENT_SECRET=your_client_secret_here
OURA_REDIRECT_URI=http://localhost:8000/callback

# Database Settings
DATABASE_URL=postgresql://username:password@localhost:5432/oura_data
# Or use individual components:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=oura_data
# DB_USER=postgres
# DB_PASSWORD=your_password

# Application Settings
LOG_LEVEL=INFO
SYNC_DAYS_BACK=90
```

3. **Create PostgreSQL database**

Many ways to handle this. I suggest a docker container with some pre-configuration.
By default, name your database oura_sync.

## Getting Started

### 1. Initialize the Database

```bash
python scripts/init_db.py
```

This creates all necessary tables in your PostgreSQL database.

### 2. Authenticate with Oura

```bash
python scripts/authenticate.py
```

This will:
1. Open your browser to Oura's authorization page
2. Ask you to grant permissions (select all scopes you need)
3. Redirect you to `http://localhost:8000/callback?code=...`
4. Prompt you to paste the authorization code (stop before &session)
5. Exchange the code for OAuth tokens and store them securely

**Note:** The redirect won't load a page (that's expected). Just copy the `code=` value from the URL.

### 3. Sync Your Data

```bash
# Initial sync - get last 90 days of all data
python scripts/sync_data.py --initial --all

# Sync specific date range
python scripts/sync_data.py --start-date 2024-01-01 --end-date 2024-01-31

# Sync specific data types
python scripts/sync_data.py --types daily_sleep,daily_activity,heart_rate

# Sync today's data (useful for daily cron jobs)
python scripts/sync_data.py
```

## Usage

### Command Line Options

```bash
python scripts/sync_data.py [OPTIONS]

Options:
  --initial              Sync from SYNC_DAYS_BACK days ago to today
  --all                  Sync all data types
  --start-date DATE      Start date (YYYY-MM-DD)
  --end-date DATE        End date (YYYY-MM-DD)
  --types TYPE1,TYPE2    Comma-separated list of data types to sync
  --user-id USER_ID      Specific user ID (default: uses first authenticated user)
```

### Programmatic Usage

```python
from services.oura_client import OuraClient
from services.oauth import OuraOAuth
from utils.database import get_db

# Create an authenticated client
client = OuraClient(user_id="your_user_id")

# Fetch data
sleep_data = client.get_daily_sleep("2024-01-01", "2024-01-31")
activity_data = client.get_daily_activity("2024-01-01", "2024-01-31")
heart_rate_data = client.get_heart_rate("2024-01-01T00:00:00", "2024-01-31T23:59:59")

# Access personal info
personal_info = client.get_personal_info()

# The client automatically:
# - Refreshes tokens when they expire
# - Handles rate limiting (429 errors)
# - Retries failed requests with exponential backoff
# - Paginates large result sets

# Work with the database
with get_db() as db:
    from models.daily_sleep import DailySleep

    # Query data
    recent_sleep = db.query(DailySleep).filter(
        DailySleep.user_id == "your_user_id"
    ).order_by(DailySleep.day.desc()).limit(7).all()
```

## Data Types

The service supports all Oura API v2 data types:

### Daily Summaries
- `daily_activity` - Activity score, steps, calories, active time
- `daily_sleep` - Sleep score, duration, efficiency, contributors
- `daily_readiness` - Readiness score and contributing factors
- `daily_spo2` - Blood oxygen saturation levels
- `daily_stress` - Daytime stress measurements
- `daily_resilience` - Resilience metrics and trends
- `daily_cardiovascular_age` - Cardiovascular age estimates

### Time Series Data
- `heart_rate` - 5-minute interval heart rate samples

### Sessions & Events
- `sleep` - Individual sleep sessions with detailed stages
- `sleep_time` - Optimal bedtime recommendations
- `workout` - Workout sessions with intensity and heart rate
- `session` - Guided sessions (meditation, breathing, etc.)
- `tag` - User-entered tags and moments
- `enhanced_tag` - Enhanced tags with additional context

### Profile & Device
- `personal_info` - Age, weight, height, biological sex, email
- `ring_configuration` - Ring model, size, color, firmware version
- `rest_mode_period` - Rest mode activation periods
- `vo2_max` - VO2 max estimates and trends

## Database Schema

All tables include automatic timestamp tracking (`created_at`, `updated_at`):

```sql
-- Authentication
oauth_tokens (user_id, access_token, refresh_token, expires_at, scopes)

-- Profile
personal_info (id, user_id, age, weight, height, biological_sex, email, raw_data)

-- Daily Summaries
daily_activity (id, user_id, day, raw_data)
daily_sleep (id, user_id, day, raw_data)
daily_readiness (id, user_id, day, raw_data)
daily_spo2 (id, user_id, day, raw_data)
daily_stress (id, user_id, day, raw_data)
daily_resilience (id, user_id, day, raw_data)
daily_cardiovascular_age (id, user_id, day, raw_data)

-- Time Series
heart_rate (id, user_id, timestamp, raw_data)

-- Sessions
sleep (id, user_id, day, raw_data)
sleep_time (id, user_id, day, raw_data)
workout (id, user_id, day, raw_data)
session (id, user_id, day, raw_data)
tag (id, user_id, day, raw_data)
enhanced_tag (id, user_id, day, raw_data)

-- Device
rest_mode_period (id, user_id, raw_data)
ring_configuration (id, user_id, raw_data)
vo2_max (id, user_id, day, raw_data)
```

**Note:** Current models store complete API responses in `raw_data` as JSON. You can expand these models to extract specific fields into dedicated columns for easier querying.

### Expanding Models Example

```python
# models/daily_activity.py
from sqlalchemy import String, Integer, Float, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailyActivity(Base, OuraBaseMixin):
    __tablename__ = "daily_activity"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Extracted fields
    score: Mapped[int | None] = mapped_column(Integer)
    active_calories: Mapped[int | None] = mapped_column(Integer)
    steps: Mapped[int | None] = mapped_column(Integer)

    # Full data for reference
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)
```

## Scheduling

### Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add daily sync at 8 AM
0 8 * * * cd /path/to/oura_sync && /path/to/venv/bin/python scripts/sync_data.py >> logs/cron.log 2>&1
```

### Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task - "Oura Daily Sync"
3. Trigger: Daily at 8:00 AM
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `scripts\sync_data.py`
   - Start in: `C:\path\to\oura_sync`

### systemd Timer (Linux)

Create `/etc/systemd/system/oura-sync.service`:

```ini
[Unit]
Description=Oura Ring Data Sync
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/oura_sync
ExecStart=/path/to/venv/bin/python scripts/sync_data.py
```

Create `/etc/systemd/system/oura-sync.timer`:

```ini
[Unit]
Description=Daily Oura Ring Data Sync
Requires=oura-sync.service

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl enable oura-sync.timer
sudo systemctl start oura-sync.timer
```

## Troubleshooting

### Authentication Issues

**"No valid authentication for user"**
- Run `python scripts/authenticate.py` to set up OAuth tokens
- Ensure you copied the full authorization code from the redirect URL

**"Token exchange failed: (insecure_transport)"**
- This should be handled automatically for localhost
- If you see this, check that `OURA_REDIRECT_URI` starts with `http://localhost` or `http://127.0.0.1`

**"Scope has changed from X to extapi:X"**
- This is normal - Oura prefixes scopes with `extapi:` in responses
- The code handles this automatically via `OAUTHLIB_RELAX_TOKEN_SCOPE`

### Database Issues

**"can't subtract offset-naive and offset-aware datetimes"**
- This has been fixed - the code now uses timezone-aware datetimes consistently
- If you see this, ensure you're using the latest version

**"Database connection failed"**
- Check PostgreSQL is running: `pg_isready`
- Verify `DATABASE_URL` in `.env`
- Test connection: `psql $DATABASE_URL`

### API Issues

**Rate limiting (429 errors)**
- The client handles this automatically with `Retry-After` header
- Oura's rate limit: ~5,000 requests per day

**"No data returned"**
- Check the date range - Oura typically provides data from the past 2 years
- Verify your ring has been synced to the app
- Some data types (like `vo2_max`) require specific conditions

### Token Refresh Issues

**"Failed to refresh token"**
- Oura refresh tokens are single-use
- The code handles this correctly
- If you see repeated failures, re-authenticate: `python scripts/authenticate.py`

## Project Structure

```
oura_sync/
├── config/
│   ├── __init__.py
│   └── settings.py          # Pydantic settings management
├── models/
│   ├── __init__.py
│   ├── base.py              # Base model with timestamps
│   ├── auth.py              # OAuth token model
│   ├── personal_info.py     # Personal info model
│   ├── daily_*.py           # Daily summary models
│   ├── sleep.py             # Sleep session model
│   ├── workout.py           # Workout model
│   └── ...                  # Other data type models
├── services/
│   ├── oauth.py             # OAuth2 authentication (requests-oauthlib)
│   └── oura_client.py       # Oura API client
├── scripts/
│   ├── authenticate.py      # OAuth setup script
│   ├── init_db.py           # Database initialization
│   └── sync_data.py         # Data sync script
├── utils/
│   ├── __init__.py
│   ├── database.py          # Database connection management
│   └── logger.py            # Colored logging setup
├── logs/                    # Application logs (created automatically)
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Security Considerations

- **Never commit `.env`** - It contains sensitive credentials
- **OAuth tokens** - Stored securely in PostgreSQL with proper access controls
- **HTTPS in production** - Use HTTPS redirect URIs in production environments
- **Token refresh** - Automatic handling of single-use refresh tokens
- **CSRF protection** - State parameter validation in OAuth flow

## Advanced Usage

### Using OAuth2Session for API Calls

The `OuraClient` uses `OAuth2Session` by default for automatic token refresh:

```python
# Automatic token refresh enabled (default)
client = OuraClient(user_id="your_user_id", use_oauth_session=True)

# Legacy mode (manual token management)
client = OuraClient(user_id="your_user_id", use_oauth_session=False)
```

### Custom Data Processing

```python
from services.oura_client import OuraClient
from utils.database import get_db
from models.daily_sleep import DailySleep
import json

client = OuraClient(user_id="your_user_id")
sleep_data = client.get_daily_sleep("2024-01-01", "2024-01-31")

with get_db() as db:
    for item in sleep_data:
        sleep = DailySleep(
            id=item["id"],
            user_id="your_user_id",
            day=item["day"],
            raw_data=json.dumps(item)
        )
        db.merge(sleep)  # Insert or update
```

### Webhook Implementation (Recommended)

For production deployments, implement webhooks instead of polling:

1. Create a webhook endpoint (Flask/FastAPI)
2. Register with Oura: `POST /v2/webhook/subscription`
3. Verify webhook signatures
4. Process data updates in near real-time (30s latency)

See [Oura Webhook Documentation](https://cloud.ouraring.com/docs/webhooks) for details.

## Contributing

Contributions are welcome! Areas for improvement:

1. **Expand database models** - Extract specific fields from `raw_data`
2. **Add webhook support** - Real-time data updates
3. **Data visualization** - Create dashboards and reports
4. **Additional sync strategies** - Incremental updates, backfill logic
5. **Tests** - Unit and integration tests
6. **Documentation** - API reference, model schemas

## License

Apache License 2.0

## Acknowledgments

- Built with [requests-oauthlib](https://github.com/requests/requests-oauthlib) for OAuth2
- Uses [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
- Oura API documentation: [https://cloud.ouraring.com/docs/](https://cloud.ouraring.com/docs/)

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review [Oura API Documentation](https://cloud.ouraring.com/docs/)
- Open an issue on GitHub

---
