# AI Browser Automation Chat Interface

A web application that combines a chat interface with browser automation capabilities using E2B sandbox environment.

## Project Structure

```
.
├── frontend/           # Next.js frontend application
│   ├── components/    # React components
│   ├── pages/         # Next.js pages
│   └── styles/        # CSS styles
├── backend/           # FastAPI backend server
│   ├── app/          # Application code
│   └── tests/        # Test files
├── mobile/            # React Native mobile app (Expo)
└── README.md         # This file
```

## Technologies Used

### Frontend
- Next.js 14
- Chakra UI
- TypeScript
- Axios for API calls

### Backend
- FastAPI
- Python 3.9+
- E2B Desktop
- Browser automation tools

## Prerequisites

- Node.js 18+
- Python 3.9+
- npm or yarn
- pip

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Set up environment variables:
Create `.env` files in both frontend and backend directories with the necessary API keys and configurations.

5. Start the backend server:
```bash
cd backend
uvicorn app.main:app --reload
```

6. Start the frontend development server:
```bash
cd frontend
npm run dev
```

7. Start the mobile app (Expo):
```bash
cd mobile
npm install
npm start
```

The application will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
E2B_API_KEY=your_e2b_api_key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Mobile (.env)
```
EXPO_PUBLIC_API_URL=http://localhost:8000
```

## Features

- Real-time chat interface
- Browser automation visualization
- Task history tracking
- Responsive design

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 