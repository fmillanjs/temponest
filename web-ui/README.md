# Temponest Web UI - Admin Dashboard

Simple web-based admin dashboard for managing the Temponest Agentic Platform.

## Features

- **Dashboard Overview**: Real-time metrics and status
- **Agent Management**: Create, view, execute, and delete agents
- **Schedule Management**: Create and manage scheduled tasks
- **Cost Tracking**: View cost summaries and trends
- **Dark Theme**: Modern, easy-on-the-eyes interface

## Installation

```bash
cd /home/doctor/temponest/web-ui
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export TEMPONEST_BASE_URL=http://localhost:9000
export TEMPONEST_AUTH_TOKEN=your-token-here
```

Or create a `.env` file:

```
TEMPONEST_BASE_URL=http://localhost:9000
TEMPONEST_AUTH_TOKEN=your-token-here
```

## Running

```bash
python app.py
```

The dashboard will be available at: http://localhost:8080

## Usage

### Dashboard Page

The main dashboard shows:
- Total number of agents
- Total number of active schedules
- Total cost for the last 30 days
- Service health status
- Recent agents and schedules

### Managing Agents

1. **Create Agent**: Click "Create Agent" button
2. **Execute Agent**: Click "Execute" on any agent row
3. **Delete Agent**: Click "Delete" on any agent row

### Managing Schedules

1. **Create Schedule**: Click "Create Schedule" button
2. **Delete Schedule**: Click "Delete" on any schedule row

## Production Deployment

For production, use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

Or with Docker:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
```

## Security Notes

- Always use HTTPS in production
- Set strong authentication tokens
- Use environment variables for sensitive config
- Implement proper authentication/authorization
- Add rate limiting for API endpoints
