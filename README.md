# Art Chatbot

## Description

An AI-powered art chatbot application that enables users to engage in interactive conversations and generate artistic images based on their dialogue. The application combines natural language processing with image generation capabilities to create a unique creative experience.

Built with a Django REST API backend and a React frontend, featuring user authentication, conversation management, and image processing.

## Features

- **User Authentication**: Secure login and registration system using JWT tokens
- **Conversation Management**: Create, view, update, and delete chat conversations
- **Real-time Chat Interface**: Interactive messaging with conversation history
- **Image Processing**: Generate artistic images based on conversation context
- **Mood-Based Color Mappings**: Dynamic color schemes based on conversation mood
- **Fast Inference**: ONNX model integration for optimized performance
- **Cloud Storage**: Image storage and management via Cloudinary
- **Responsive Design**: Modern React frontend with mobile-friendly interface

## Tech Stack

### Backend
- **Django 5.2**: Web framework
- **Django REST Framework**: API development
- **JWT Authentication**: Secure token-based auth
- **PostgreSQL**: Database (via dj-database-url)
- **Cloudinary**: Media storage and management
- **ONNX Runtime**: Optimized model inference
- **HuggingFace Transformers**: AI language model integration
- **Spacy**: Natural language processing
- **Gunicorn**: WSGI server for production

### Frontend
- **React 19**: UI library
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **Axios**: HTTP client for API calls
- **ESLint**: Code linting

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- PostgreSQL database
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd art-chatbot/chatbot
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the `chatbot/` directory with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DB_URL=postgresql://user:password@localhost:5432/dbname
   ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
   CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```
   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173` (Vite default)

## Usage

1. **Access the Application**
   - Open your browser and navigate to the frontend URL (default: `http://localhost:5173`)
   - The app will redirect to `/chat`

2. **User Registration/Login**
   - Register a new account or login with existing credentials
   - JWT tokens handle authentication automatically

3. **Start Chatting**
   - Create a new conversation or select an existing one
   - Send messages in the chat interface
   - The chatbot will respond and may generate images based on the conversation

4. **Image Generation**
   - Images are generated based on conversation context
   - Stored securely via Cloudinary integration

## API Documentation

The backend provides a REST API with the following endpoints:

### Authentication
- `POST /api/token/` - Obtain JWT tokens
- `POST /api/token/refresh/` - Refresh access token

### Conversations
- `GET /api/conversations/` - List all user conversations
- `POST /api/conversations/` - Create a new conversation
- `PUT /api/conversations/<id>/` - Update conversation details
- `DELETE /api/conversations/<id>/` - Delete a conversation

### Messages
- `GET /api/chat/<conv_id>/` - Get all messages in a conversation
- `POST /api/chat/<conv_id>/message/` - Send a new message

### Session
- `POST /api/init/` - Initialize user session

All endpoints require authentication except token endpoints.

## Project Structure

```
art-chatbot/
├── chatbot/                    # Django backend
│   ├── chatbot/               # Main Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── chats/                 # Main app
│   │   ├── models/           # Database models
│   │   ├── views.py          # API views
│   │   ├── urls.py           # URL routing
│   │   └── management/       # Custom management commands
│   ├── embeddings/           # AI model embeddings
│   ├── onnx_model/           # ONNX model files
│   ├── requirements.txt      # Python dependencies
│   └── manage.py
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   └── api.js           # API client
│   ├── package.json          # Node dependencies
│   └── vite.config.js       # Vite configuration
└── README.md
```

## Development

### Running Tests
```bash
# Backend tests
cd chatbot
python manage.py test

# Frontend tests (if configured)
cd frontend
npm test
```

### Building for Production

**Backend:**
```bash
# Using gunicorn
gunicorn chatbot.wsgi --bind 0.0.0.0:8000
```

**Frontend:**
```bash
npm run build
# Serve the dist/ folder with a static server
```

### Environment Variables

Key environment variables for production:
- `DEBUG=False`
- `SECRET_KEY` - Django secret key
- `DB_URL` - Database connection string
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `CLOUDINARY_URL` - Cloudinary configuration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions or issues, please open an issue on the GitHub repository.