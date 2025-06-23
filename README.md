# Hakka AI Podcast Generator

An AI-powered personalized Hakka podcast generator that creates custom podcast content using advanced AI technologies.

## Tech Stack

### Frontend
- Vue.js 3 with Composition API
- Vite for build tooling
- Tailwind CSS for styling
- shadcn-vue for UI components

### Backend
- FastAPI for API development
- Pydantic AI framework for AI operations
- Google Gemini for content generation

## Project Structure

```
hakka-podcast-generator/
├── frontend/          # Vue.js frontend application
├── backend/           # FastAPI backend application
└── README.md         # Project documentation
```

## Features

- **3-Step AI Pipeline**: Traditional Chinese → Hakka Translation → Hakka TTS
- **Official Hakka AI Integration**: Uses Hakka AI Hackathon APIs
- **Authentic Hakka Content**: Real translation and pronunciation
- **Multi-format Display**: Chinese, Hakka text, and romanization
- **Audio Generation**: High-quality Hakka speech synthesis
- **Modern Web Interface**: Responsive Vue.js frontend
- **Docker Support**: Easy deployment and development

## Quick Start with Docker

1. Clone the project and navigate to the directory
2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
3. Configure your API credentials in the `.env` file:
   - **Gemini API key** for content generation
   - **Hakka AI credentials** for translation and TTS (uses official endpoints)
4. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Development

### Docker Development Mode

For development with hot reloading:
```bash
docker-compose --profile dev up --build
```

This will start:
- Frontend dev server: http://localhost:5173
- Backend dev server: http://localhost:8001

### Manual Setup

See individual README files in `frontend/` and `backend/` directories for manual setup instructions.