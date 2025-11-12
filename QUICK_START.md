# Oura Ring Data Sync - Quick Start Guide

A complete Python service for syncing your Oura Ring data to a PostgreSQL database with OAuth2 authentication. The project includes:

### Core Components

1. **OAuth2 Authentication** (`services/oauth.py`)
   - Handles the complete OAuth2 flow
   - Automatically refreshes expired tokens
   - Securely stores tokens in database

2. **Oura API Client** (`services/oura_client.py`)
   - Comprehensive API client for all Oura endpoints
   - Automatic retry logic with exponential backoff
   - Rate limit handling
   - Pagination support

3. **Database Models** (`models/`)
   - SQLAlchemy models for all data types
   - Base models with timestamps
   - OAuth token storage
   - Personal info, daily summaries, time-series data

4. **Utilities** (`utils/`)
   - Database connection management
   - Colored logging with file output
   - Configuration management

5. **Scripts** (`scripts/`)
   - `authenticate.py` - Initial OAuth setup
   - `init_db.py` - Database initialization
   - `sync_data.py` - Daily data sync

## Setup Instructions

### 1. Install Dependencies

```bash
cd oura_sync
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Get these from https://cloud.ouraring.com/oauth/applications
OURA_CLIENT_ID=your_client_id_here
OURA_CLIENT_SECRET=your_client_secret_here
OURA_REDIRECT_URI=http://localhost:8000/callback

# Your PostgreSQL database
DATABASE_URL=postgresql://username:password@localhost:5432/oura_data
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

This creates all necessary tables in your PostgreSQL database.

### 4. Authenticate with Oura

```bash
python scripts/authenticate.py
```

This will:
- Open your browser to Oura's authorization page
- Ask you to grant permissions
- Store your OAuth tokens securely

### 5. Sync Your Data

```bash
# Initial sync (last 90 days of all data)
python scripts/sync_data.py --initial --all

# Sync specific date range
python scripts/sync_data.py --start-date 2024-01-01 --end-date 2024-01-31

# Sync specific data types
python scripts/sync_data.py --types daily_sleep,daily_activity,heart_rate
```

## What Data Can You Sync?

The service supports all Oura API v2 data types:

### Daily Summaries
- `daily_activity` - Activity score, steps, calories
- `daily_sleep` - Sleep score and contributors
- `daily_readiness` - Readiness score and factors
- `daily_spo2` - Blood oxygen levels
- `daily_stress` - Daytime stress measurements
- `daily_resilience` - Resilience metrics
- `daily_cardiovascular_age` - Cardiovascular age estimates

### Time Series Data
- `heart_rate` - 5-minute heart rate samples

### Sessions & Events
- `sleep` - Individual sleep sessions
- `workout` - Workout details
- `session` - Guided/unguided sessions
- `tag` - User-entered tags
- `enhanced_tag` - Enhanced tags with context

### Other Data
- `personal_info` - Age, weight, height, etc.
- `ring_configuration` - Ring model, size, firmware
- `rest_mode_period` - Rest mode periods
- `sleep_time` - Optimal bedtime recommendations
- `vo2_max` - VO2 max estimates

## Database Schema

The service creates the following tables:

```
oauth_tokens              - OAuth token storage
personal_info            - User personal information
daily_activity           - Daily activity summaries
daily_sleep              - Daily sleep summaries
daily_readiness          - Daily readiness scores
daily_spo2               - Daily SpO2 measurements
daily_stress             - Daily stress data
daily_resilience         - Daily resilience scores
daily_cardiovascular_age - Cardiovascular age estimates
heart_rate               - Time-series heart rate data
sleep                    - Individual sleep sessions
sleep_time               - Sleep time recommendations
workout                  - Workout sessions
session                  - App sessions
tag                      - User tags
enhanced_tag             - Enhanced tags
rest_mode_period         - Rest mode periods
ring_configuration       - Ring configuration data
vo2_max                  - VO2 max estimates
```

## Scheduling Daily Syncs

### Using Cron (Linux/Mac)

```bash
# Add to crontab (opens editor)
crontab -e

# Add this line to sync daily at 8 AM
0 8 * * * cd /path/to/oura_sync && /path/to/python scripts/sync_data.py >> logs/cron.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 8:00 AM)
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `C:\path\to\oura_sync\scripts\sync_data.py`
7. Start in: `C:\path\to\oura_sync`

## Next Steps - Expanding the Models

The current models are stubs that store raw JSON data. 
For example:

### Expanding DailyActivity Model

```python
# models/daily_activity.py
from sqlalchemy import String, Integer, Float, Text, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailyActivity(Base, OuraBaseMixin):
    __tablename__ = "daily_activity"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Core metrics
    score: Mapped[int] = mapped_column(Integer, nullable=True)
    active_calories: Mapped[int] = mapped_column(Integer, nullable=True)
    average_met_minutes: Mapped[float] = mapped_column(Float, nullable=True)
    steps: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Activity levels
    high_activity_time: Mapped[int] = mapped_column(Integer, nullable=True)
    medium_activity_time: Mapped[int] = mapped_column(Integer, nullable=True)
    low_activity_time: Mapped[int] = mapped_column(Integer, nullable=True)
    sedentary_time: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Contributors (as JSON)
    contributors: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Store full data for reference
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
```

Repeat this process for each model based on the API schema provided.

## Troubleshooting

### "No authentication found"
Run `python scripts/authenticate.py` first

### "Token expired"
The service automatically refreshes tokens, but if this fails, re-run authentication

### Database connection errors
Check your DATABASE_URL in .env and ensure PostgreSQL is running

### Rate limit errors
The service handles rate limits automatically with exponential backoff

## Advanced Usage

### Programmatic Access

```python
from services.oura_client import OuraClient
from utils import get_db

# Create client
client = OuraClient(user_id="your_user_id")

# Fetch data
sleep_data = client.get_daily_sleep("2024-01-01", "2024-01-31")
activity_data = client.get_daily_activity("2024-01-01", "2024-01-31")

# Work with database
with get_db() as db:
    # Your database operations
    pass
```

### Implementing Webhooks (Recommended)

For production use, implement webhooks instead of polling:

1. Set up a webhook endpoint on your server
2. Register webhooks with Oura API
3. Receive near real-time updates (30s after sync)

See the README for webhook implementation details.

## Project Structure

```
oura_sync/
├── config/           # Configuration management
├── models/           # Database models
├── services/         # OAuth & API client
├── scripts/          # CLI scripts
├── utils/            # Utilities
├── data/             # Downloaded data (created on sync)
├── logs/             # Application logs
└── requirements.txt
```