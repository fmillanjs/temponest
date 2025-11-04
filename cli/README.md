# Temponest CLI

Command-line tool for managing the Temponest Agentic Platform.

## Installation

```bash
cd /home/doctor/temponest/cli
pip install -e .
```

## Configuration

Set environment variables:

```bash
export TEMPONEST_BASE_URL=http://localhost:9000
export TEMPONEST_AUTH_TOKEN=your-token-here
```

Or create a `.env` file:

```bash
TEMPONEST_BASE_URL=http://localhost:9000
TEMPONEST_AUTH_TOKEN=your-token-here
```

## Usage

### General

```bash
# Check platform status
temponest status

# Get help
temponest --help
```

### Agent Management

```bash
# List agents
temponest agent list
temponest agent list --limit 50
temponest agent list --search "assistant"

# Create an agent
temponest agent create \
  --name "MyAgent" \
  --model "llama3.2:latest" \
  --description "A helpful assistant" \
  --system-prompt "You are a helpful AI assistant"

# Get agent details
temponest agent get <agent-id>

# Execute an agent
temponest agent execute <agent-id> "Hello, how are you?"

# Execute with streaming
temponest agent execute <agent-id> "Tell me a story" --stream

# Delete an agent
temponest agent delete <agent-id>
```

### Schedule Management

```bash
# List schedules
temponest schedule list
temponest schedule list --agent-id <agent-id>
temponest schedule list --active-only

# Create a schedule
temponest schedule create \
  --agent-id <agent-id> \
  --cron "0 9 * * *" \
  --message "Generate daily report"

# Pause/resume schedule
temponest schedule pause <schedule-id>
temponest schedule resume <schedule-id>

# Manually trigger a schedule
temponest schedule trigger <schedule-id>

# Delete a schedule
temponest schedule delete <schedule-id>
```

### Cost Tracking

```bash
# View cost summary
temponest cost summary
temponest cost summary --days 7

# View budget status
temponest cost budget

# Set budget limits
temponest cost set-budget --daily 50.0 --monthly 1000.0
temponest cost set-budget --daily 100.0 --threshold 0.8
```

## Examples

### Create and Execute an Agent

```bash
# Create agent
AGENT_ID=$(temponest agent create \
  --name "DataAnalyst" \
  --model "llama3.2:latest" \
  --system-prompt "You are a data analyst" | grep "ID:" | awk '{print $2}')

# Execute agent
temponest agent execute $AGENT_ID "Analyze this data: [1,2,3,4,5]"
```

### Schedule Daily Reports

```bash
# Create agent
AGENT_ID=$(temponest agent create \
  --name "Reporter" \
  --model "llama3.2:latest" | grep "ID:" | awk '{print $2}')

# Schedule daily at 9 AM
temponest schedule create \
  --agent-id $AGENT_ID \
  --cron "0 9 * * *" \
  --message "Generate today's summary report"
```

### Monitor Costs

```bash
# Check weekly costs
temponest cost summary --days 7

# Set budget alert at 80% of $100/day
temponest cost set-budget --daily 100.0 --threshold 0.8

# Check current budget status
temponest cost budget
```

## Features

- **Rich Terminal UI**: Beautiful tables and colored output
- **Streaming Support**: Real-time streaming for agent responses
- **Interactive Confirmations**: Safety prompts for destructive operations
- **Status Monitoring**: Check health of all platform services
- **Cost Management**: Track and manage AI costs and budgets
- **Comprehensive Help**: Built-in help for all commands

## Tips

- Use `temponest <command> --help` to get detailed help for any command
- Most list commands support `--limit` to control output
- Use `--confirmation` flag to skip confirmation prompts in scripts
- Set environment variables in `.bashrc` or `.zshrc` for persistent config
