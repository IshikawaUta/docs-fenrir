# Monitoring Dashboard

Fenrir v3.1.2 includes a built-in monitoring dashboard for tracking application health, traffic analysis, and alerts. The dashboard is powered by `fenrir.features.init_fenrir_monitoring()` and provides both a web UI and REST API endpoints.

---

## Quick Setup

### 1. Enable Monitoring in Your App

```python
from fenrir import Fenrir
from fenrir.features import init_fenrir_monitoring

app = Fenrir(title="My App", version="3.1.2")

# Enable the monitoring dashboard
init_fenrir_monitoring(app)
```

### 2. Configure via Environment Variables

```bash
MONITORING_ENABLED=true
MONITORING_USER=admin
MONITORING_PASSWORD=changeme
MONITORING_SECRET_KEY=your-random-secret-key
MONITORING_SITES=http://localhost:8000,https://example.com
MONITORING_CHECK_INTERVAL=60
```

### 3. Access the Dashboard

Navigate to `/monitoring` in your browser. You will be redirected to the login page.

**Default credentials:**

- Username: `admin`
- Password: `changeme`

> **Important:** Change the default password in production using `fenrir monitoring set-password` or by setting `MONITORING_PASSWORD` in your `.env` file.

---

## CLI Management

Fenrir provides CLI commands to manage the monitoring dashboard:

```bash
# Enable monitoring
fenrir monitoring enable

# Disable monitoring
fenrir monitoring disable

# Show monitoring configuration status
fenrir monitoring status

# Set a new dashboard password
fenrir monitoring set-password
```

---

## Dashboard Features

### Health Checks

The dashboard periodically checks the health of configured sites. Health checks run asynchronously using a thread pool to avoid blocking the event loop.

### Traffic Analysis

Every incoming request is recorded with:

- Path and HTTP method
- Response status code
- Response time (milliseconds)
- Timestamp

### Statistics

The dashboard provides real-time statistics:

- Total requests today vs. yesterday
- Error rate percentage
- Average response time
- Active alerts

### Uptime Tracking

Uptime percentage is calculated for each monitored site based on health check history. The dashboard displays uptime status with visual indicators.

### Alerts

The system generates alerts at different levels:

- **Info**: General information messages
- **Warning**: Potential issues (e.g., high response times)
- **Error**: Critical failures (e.g., site unreachable)

---

## API Endpoints

All monitoring API endpoints require authentication via the `monitoring_token` cookie.

### `GET /monitoring/api/stats`

Returns traffic statistics, site counts, and uptime start time.

```json
{
  "total_requests_today": 1234,
  "total_requests_yesterday": 1100,
  "error_rate": 2.3,
  "avg_response_time": 45.2,
  "monitored_sites": 3,
  "uptime_start": "2024-01-15T10:30:00Z"
}
```

### `GET /monitoring/api/traffic`

Returns today vs. yesterday traffic comparison.

```json
{
  "today": { "total": 1234, "errors": 28 },
  "yesterday": { "total": 1100, "errors": 22 }
}
```

### `GET /monitoring/api/alerts?limit=50`

Returns recent alerts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Number of alerts to return (1-500) |

### `GET /monitoring/api/health`

Triggers health checks on all monitored sites and returns results.

### `GET /monitoring/api/uptime`

Returns uptime percentage for each monitored site.

```json
{
  "sites": [
    { "url": "http://localhost:8000", "uptime": 99.9, "checks": 1440 },
    { "url": "https://example.com", "uptime": 99.5, "checks": 1440 }
  ]
}
```

### `GET /monitoring/api/response-times?url=...&hours=24`

Returns response time history for a specific site.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | The site URL to check |
| `hours` | int | No | Hours of history (max 168, default 24) |

### `GET /monitoring/api/hourly?hours=24`

Returns hourly traffic breakdown.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours` | int | 24 | Hours of history (max 720) |

### `GET /monitoring/api/summary`

Returns a comprehensive summary with overview, sites, alerts, and hourly traffic data.

### `POST /monitoring/api/check`

Check health of a specific site.

```json
{
  "url": "http://example.com"
}
```

---

## Integration Example

### Complete Setup with Custom Configuration

```python
import os
import logging
from fenrir import Fenrir
from fenrir.features import init_fenrir_monitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myapp")

app = Fenrir(title="Production App", version="3.1.2")

# Configure monitoring via environment
# Or pass configuration directly:
init_fenrir_monitoring(
    app,
    enabled=os.getenv("MONITORING_ENABLED", "true") == "true",
    user=os.getenv("MONITORING_USER", "admin"),
    password=os.getenv("MONITORING_PASSWORD", "changeme"),
    secret_key=os.getenv("MONITORING_SECRET_KEY", "dev-secret"),
    sites=os.getenv("MONITORING_SITES", "http://localhost:8000").split(","),
    check_interval=int(os.getenv("MONITORING_CHECK_INTERVAL", "60")),
)

@app.get("/")
async def index():
    return {"status": "ok"}

@app.get("/api/data")
async def get_data():
    return {"data": [1, 2, 3]}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, app_path="app:app")
```

### Using CLI to Enable Monitoring

```bash
# Enable monitoring from the command line
fenrir monitoring enable

# Set a secure password
fenrir monitoring set-password

# Check the status
fenrir monitoring status

# Run the app
fenrir run app:app --dev
```

---

## Data Persistence

Monitoring data is stored locally in the `.fenrir_monitoring/` directory:

```
.fenrir_monitoring/
└── monitoring_data.json
```

This file contains:

- Traffic logs
- Health check history
- Alert records
- Configuration state

---

## Security Considerations

1. **Change default credentials** before deploying to production.
2. **Use HTTPS** in production to protect the monitoring token cookie.
3. **Restrict access** to the `/monitoring` path using network rules or middleware.
4. **Set a strong `MONITORING_SECRET_KEY`** for secure session management.
5. **Monitor the monitoring endpoint** itself — consider adding rate limiting.

---

## Performance Notes

- Health checks run asynchronously using `asyncio.to_thread()` to avoid blocking the main event loop.
- Traffic data is stored in-memory and periodically flushed to disk.
- The monitoring middleware adds minimal overhead (~0.1ms per request).
