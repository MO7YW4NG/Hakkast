# Hakka AI Podcast Generator - Backend

FastAPI backend service implementing a 3-step AI pipeline for generating personalized Hakka podcasts using **official Hakka AI Hackathon APIs**:

1. **Traditional Chinese Generation** using Gemini AI
2. **Chinese to Hakka Translation** using `https://hktrans.bronci.com.tw`
3. **Hakka Text-to-Speech** using `https://hktts.bronci.com.tw`

## Features

- FastAPI REST API with async support
- Real Hakka AI Hackathon API integration
- Google Gemini AI for content generation
- Automatic authentication and session management
- Fallback mechanisms for robustness
- CORS enabled for frontend integration
- Static file serving for audio files

## API Pipeline

### Step 1: Content Generation
- Uses Gemini AI to generate Traditional Chinese podcast scripts
- Culturally appropriate prompts focused on Hakka themes
- Customizable tone, duration, and topics

### Step 2: Translation
- Integrates with Hakka AI Hackathon translation API
- Converts Traditional Chinese to authentic Hakka text
- Includes romanization generation

### Step 3: Audio Synthesis  
- Uses Hakka AI Hackathon TTS service
- Generates high-quality Hakka speech audio
- Supports multiple voice models

## Setup

### Prerequisites
- Python 3.11+
- Access to Hakka AI Hackathon APIs
- Google Gemini API key

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

Required environment variables:
```bash
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Hakka AI Hackathon APIs (using official endpoints)
HAKKA_USERNAME=your_hakka_username
HAKKA_PASSWORD=your_hakka_password
HAKKA_TTS_API_URL=https://hktts.bronci.com.tw
HAKKA_TRANSLATE_API_URL=https://hktrans.bronci.com.tw
```

3. Run the development server:
```bash
python run.py
```

The API will be available at http://localhost:8000

## API Documentation

- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## API Endpoints

### Podcast Management
- `POST /api/podcasts/generate` - Generate a new podcast
- `GET /api/podcasts/` - Get all podcasts  
- `GET /api/podcasts/{id}` - Get specific podcast
- `DELETE /api/podcasts/{id}` - Delete podcast

### Static Files
- `GET /static/audio/{filename}` - Serve generated audio files

## Request Format

```json
{
  "topic": "客家傳統節慶",
  "tone": "educational",
  "duration": 15,
  "language": "mixed", 
  "interests": "文化歷史、傳統習俗"
}
```

## Response Format

```json
{
  "id": "uuid",
  "title": "客家傳統節慶探索",
  "chineseContent": "原始中文內容...",
  "hakkaContent": "翻譯後的客家內容...", 
  "romanization": "客語羅馬拼音...",
  "audioUrl": "/static/audio/uuid.wav",
  "audioDuration": 180,
  "createdAt": "2024-01-01T00:00:00Z"
}
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gemini AI     │───▶│  Translation     │───▶│   TTS Service   │
│ (Chinese Gen)   │    │   Service        │    │ (Audio Gen)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                       │
        ▼                        ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Podcast Service                              │
│              (Orchestrates 3-step pipeline)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

The system includes comprehensive error handling with automatic fallbacks:

- **Authentication failures**: Automatic retry and fallback to mock services
- **Network timeouts**: Graceful degradation with cached responses
- **API rate limits**: Exponential backoff and queuing
- **Service unavailability**: Mock responses to ensure functionality

## Security

- SSL verification disabled for Hakka AI APIs (as per their requirements)
- Bearer token authentication for API access
- Automatic session management and cleanup
- Input validation and sanitization
- CORS protection configured

## Monitoring

- Comprehensive logging for all API interactions
- Health check endpoints for service monitoring
- Error tracking and reporting
- Performance metrics collection

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black app/  # Code formatting
flake8 app/  # Linting
mypy app/   # Type checking
```

## Deployment

The backend is containerized and can be deployed using Docker:

```bash
docker build -t hakka-podcast-backend .
docker run -p 8000:8000 --env-file .env hakka-podcast-backend
```

For production deployment with docker-compose, see the main project README.