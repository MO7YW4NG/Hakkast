# Hakka AI Podcast Generator - Frontend

Modern Vue.js frontend for the Hakka AI Podcast Generator.

## Tech Stack

- Vue.js 3 with Composition API
- TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Vue Router for navigation
- Pinia for state management

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Run TypeScript type checking

## Features

- **Home Page**: Welcome page with feature overview
- **Generate Page**: AI podcast generation with customizable parameters
- **Library Page**: View and manage generated podcasts
- **Responsive Design**: Mobile-friendly interface
- **TypeScript Support**: Full type safety

## Project Structure

```
src/
├── components/     # Reusable Vue components
├── views/         # Page components
├── stores/        # Pinia stores
├── types/         # TypeScript type definitions
├── router/        # Vue Router configuration
└── style.css      # Global styles with Tailwind
```

## Configuration

The frontend is configured to proxy API requests to the backend server running on http://localhost:8000.