# SmartMacro AI Bot 🍽️

A Telegram bot that analyzes food images in real-time and returns detailed nutritional information using OpenAI's GPT-4o Vision.

## Features

- 📸 **Image Analysis**: Upload a food photo and get instant nutrition data
- ⚡ **Fast Response**: ~2 second analysis time
- 🎯 **Accurate Estimates**: Detailed macros including calories, protein, carbs, fats, and fiber
- 📊 **History Tracking**: View past analyses and nutrition trends
- 📅 **Daily Summaries**: See total nutrition for any day
- 📈 **Statistics**: Track your nutrition over time
- 🔄 **Async Processing**: Handles concurrent user requests efficiently
- 🐳 **Docker Ready**: Easy deployment with Docker and Docker Compose
- 🔐 **Secure**: Non-root container user, environment-based secrets

## Tech Stack

- **Python 3.11+**
- **aiogram**: Async Telegram bot framework
- **OpenAI GPT-4o**: Vision model for food analysis
- **Pydantic**: Data validation
- **Docker**: Containerized deployment

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for deployment)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key (from [OpenAI Platform](https://platform.openai.com/api-keys))

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd smart-macro-ai
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Get Your API Keys

#### Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (save it securely!)

## Deployment Options

### Option 1: Docker (Recommended for Production)

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python -m src.bot
```

## Deployment on Ubuntu Server (Vultr)

### Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
```

### Deploy the Bot

```bash
# Clone repository
git clone <repository-url>
cd smart-macro-ai

# Create .env file
cp .env.example .env
nano .env  # Edit with your API keys

# Build and start
docker-compose up -d

# Check if running
docker-compose ps

# View logs
docker-compose logs -f
```

### Update the Bot

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

## Usage

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Send a photo of your food
4. Wait ~2 seconds for nutrition analysis
5. Receive detailed macro information!

### Bot Commands

- `/start` - Welcome message and instructions
- `/help` - Usage guide and tips
- `/history [days]` - View recent meals (default: today only)
- `/today` - Today's nutrition summary
- `/week` - This week's statistics
- `/stats` - All-time statistics

## History & Statistics

The bot automatically stores all your nutrition analyses and provides powerful tracking features:

### Commands

- **`/history [days]`** - View recent meals
  - `/history` - Show today's meals
  - `/history 7` - Show last 7 days of meals
  - Displays food name, macros, and timestamps

- **`/today`** - Today's nutrition summary
  - Total calories and macros for the day
  - Number of meals analyzed
  - Daily progress tracking

- **`/week`** - This week's statistics
  - Weekly averages for all macros
  - Most commonly analyzed food
  - Total meals tracked this week

- **`/stats`** - All-time statistics
  - Total analyses count
  - Average daily nutrition
  - Top 3 most analyzed foods
  - Days tracked since you started

### Example Usage

```
You: [Send food photo]
Bot: 🍽️ Grilled Chicken - 380 kcal...

You: /today
Bot: 📅 Today's Summary - 3 meals, 1,150 kcal total...

You: /history 3
Bot: 📋 Last 3 days of meals...

You: /stats
Bot: 📊 You've tracked 147 meals since Jan 15!
```

## Project Structure

```
smart-macro-ai/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot logic and handlers
│   ├── openai_client.py    # OpenAI API integration
│   ├── prompts.py          # Nutrition analysis prompts
│   ├── config.py           # Configuration management
│   ├── models.py           # Data models
│   └── database.py         # Database operations
├── data/
│   └── nutrition.db        # SQLite database (auto-created)
├── tests/
│   ├── __init__.py
│   └── test_openai.py      # Tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | **Required** |
| `OPENAI_API_KEY` | Your OpenAI API key | **Required** |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o` |
| `MAX_TOKENS` | Max tokens for response | `500` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATABASE_PATH` | Path to SQLite database | `data/nutrition.db` |

## Database & Persistence

The bot uses SQLite to store nutrition history:

- **Location**: `data/nutrition.db` (auto-created on first run)
- **Persistence**: Data survives container restarts via Docker volume
- **Backup**: Simply copy the `data/` directory
- **Privacy**: Only stores user_id, username, and nutrition data
- **Storage**: Minimal - ~250KB per 1000 analyses

### Backup Your Data

```bash
# Backup database file
cp data/nutrition.db data/nutrition_backup.db

# Or backup entire data directory
tar -czf nutrition_backup.tar.gz data/
```

### Restore from Backup

```bash
# Stop the bot
docker-compose down

# Restore database
cp data/nutrition_backup.db data/nutrition.db

# Restart the bot
docker-compose up -d
```

## Performance

- **Response Time**: ~2 seconds per image
- **Concurrent Users**: 10-20 simultaneous requests (with default setup)
- **Cost**: ~$0.01-0.02 per image analysis (GPT-4o Vision pricing)

## Troubleshooting

### Bot not responding

```bash
# Check if container is running
docker-compose ps

# Check logs for errors
docker-compose logs -f

# Restart the bot
docker-compose restart
```

### API Errors

- Verify your API keys in `.env`
- Check OpenAI API quota: https://platform.openai.com/usage
- Ensure Telegram bot token is valid

### High Latency

- Check your server's internet connection
- Monitor OpenAI API status: https://status.openai.com/
- Consider upgrading your Vultr server specs

## Future Enhancements

- [x] Database integration for history
- [x] Daily/weekly nutrition summaries
- [ ] Export history (CSV, PDF reports)
- [ ] Nutrition goals and tracking
- [ ] Recipe support (multiple images)
- [ ] Rate limiting per user
- [ ] Redis queue for high traffic
- [ ] Web dashboard
- [ ] Data visualization (charts/graphs)

## Cost Considerations

### OpenAI API
- GPT-4o Vision: ~$0.01-0.02 per image
- 100 images/day = ~$1-2/day = ~$30-60/month

### Server (Vultr)
- Minimum: $5/month (1GB RAM, 1 vCPU)
- Recommended: $10/month (2GB RAM, 1 vCPU)

## License

MIT License - feel free to use and modify!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


---

**Built with ❤️ using Python, OpenAI GPT-4o, and aiogram**
