# FeedFinder

<div align="center">

![FeedFinder](https://img.shields.io/badge/FeedFinder-Social%20Platform-blue)
![Version](https://img.shields.io/badge/version-0.0.1-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

**A secure social media platform where users can rate profiles, share content, and support creators.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-documentation) • [Testing](#-testing) • [Security](#-security)

</div>

---

## 📖 About

FeedFinder is a modern, secure social media platform built with React and Flask. It provides users with the ability to create and share posts, rate profiles, manage privacy settings, and support creators through premium subscriptions. The application implements comprehensive security measures following OWASP best practices, including session management, CSRF protection, and role-based access control.

## ✨ Features

### User Features
- 🔐 **Secure Authentication** - Session-based authentication with Argon2 password hashing
- 👤 **User Profiles** - Customizable user profiles with statistics
- 📝 **Post Management** - Create, edit, and delete posts with media support
- 🔍 **Search Functionality** - Search posts and users across the platform
- ⭐ **Rating System** - Rate user profiles with comments
- 🔒 **Privacy Controls** - Public, private, and friends-only post privacy settings
- 👑 **Premium Membership** - Upgrade to premium for exclusive features
- 📱 **Responsive Design** - Modern, mobile-friendly UI built with Tailwind CSS

### Admin Features
- 🛡️ **Admin Panel** - Comprehensive admin interface for post management
- 👥 **User Management** - View and manage all users and posts
- 🔍 **Content Moderation** - Delete posts and manage content
- 📊 **Analytics** - View platform statistics and user activity

### Security Features
- 🔒 **Session Management** - Secure session tokens with automatic refresh
- 🛡️ **CSRF Protection** - Cross-site request forgery prevention
- 🔐 **Role-Based Access Control** - Database-verified role authorization
- 🚫 **Input Validation** - Comprehensive input validation and sanitization
- 📁 **File Validation** - Secure file upload with type and signature verification
- 🔑 **Password Security** - Argon2 password hashing with secure storage
- 🍪 **Secure Cookies** - HttpOnly, Secure, SameSite cookie attributes

## 🛠️ Tech Stack

### Frontend
- **React 18.2.0** - UI library
- **Vite 5.0.0** - Build tool and dev server
- **Tailwind CSS 3.3.0** - Utility-first CSS framework
- **Lucide React** - Icon library
- **React Router DOM 7.9.5** - Client-side routing
- **Vitest** - Unit testing framework

### Backend
- **Flask 3.1.2** - Web framework
- **MySQL** - Database
- **PyJWT 2.8.0** - JSON Web Token implementation
- **Argon2** - Password hashing
- **Flask-CORS** - Cross-origin resource sharing
- **Pytest** - Testing framework

### Security
- **Session Management** - Custom session token system
- **CSRF Protection** - Token-based CSRF prevention
- **File Validation** - Secure file upload validation
- **Input Sanitization** - XSS and injection prevention

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **MySQL** (v8.0 or higher)
- **npm** or **yarn**
- **pip** (Python package manager)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd FeedFinder
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Database Configuration

1. Create a MySQL database:
```sql
CREATE DATABASE feedfinder;
```

2. Create a `.env` file in the `backend` directory (or configure environment variables):
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=feedfinder
SECRET_KEY=your_secret_key
```

3. Import the database schema:
```bash
mysql -u your_db_user -p feedfinder < sql_stuff/latestsqlvol.sql
```

#### Run the Backend Server

```bash
cd backend
python -m flask run --port=5000
```

The backend API will be available at `http://localhost:5000`

### 3. Frontend Setup

#### Install Node Dependencies

```bash
npm install
```

#### Configure API Base URL

Create a `.env` file in the root directory:
```env
VITE_API_BASE=http://localhost:5000
```

#### Run the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Docker Setup (Optional)

You can use Docker Compose to set up the MySQL database:

```bash
cd sql_stuff
docker-compose up -d
```

## 🎯 Usage

### Starting the Application

1. **Start the MySQL database** (if not using Docker):
```bash
# Start MySQL service
sudo systemctl start mysql  # Linux
# or use your system's MySQL service manager
```

2. **Start the backend server**:
```bash
cd backend
python -m flask run --port=5000
```

3. **Start the frontend development server**:
```bash
npm run dev
```

4. **Access the application**:
   - Open your browser and navigate to `http://localhost:5173`
   - Register a new account or login with existing credentials
   - Start creating posts and exploring the platform!

### Default Admin Account

To create an admin account, you can either:
1. Manually update the database to set `user_role = 'admin'` for a user
2. Use the registration API and then update the role in the database

## 📚 API Documentation

### Authentication Endpoints

#### Login
```http
POST /api/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

#### Register
```http
POST /api/register
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123",
  "user_name": "John Doe",
  "user_email": "user@example.com"
}
```

#### Verify Session
```http
GET /api/verify-session
```

#### Logout
```http
POST /api/logout
```

### Post Endpoints

#### Create Post
```http
POST /api/posts
Content-Type: application/json
Authorization: Bearer <token>

{
  "user_id": 1,
  "content_text": "Post content",
  "media_url": "/uploads/image.jpg",
  "privacy": "public"
}
```

#### Get User Posts
```http
GET /api/posts/user/<user_id>
```

#### Get Public Posts
```http
GET /api/posts/public
```

#### Search Posts
```http
GET /api/posts/search?q=search_term
```

#### Update Post
```http
PUT /api/posts/<post_id>
Content-Type: application/json

{
  "user_id": 1,
  "content_text": "Updated content",
  "privacy": "private"
}
```

#### Delete Post
```http
DELETE /api/posts/<post_id>
```

### Profile Endpoints

#### Get Profile
```http
GET /api/profile/<user_id>
```

#### Get Profile Statistics
```http
GET /api/profile/<user_id>/stats
```

#### Update Profile
```http
PUT /api/profile/update
Content-Type: application/json

{
  "user_id": 1,
  "user_name": "New Name",
  "bio": "User bio"
}
```

### Rating Endpoints

#### Rate User
```http
POST /api/rate
Content-Type: application/json

{
  "rater_email": "rater@example.com",
  "rated_email": "rated@example.com",
  "rating": 5,
  "comment": "Great user!"
}
```

#### Get User Rating
```http
GET /api/rating/<email>
```

### Admin Endpoints

#### Get All Posts (Admin Only)
```http
GET /api/admin/posts?limit=100
Authorization: Bearer <admin_token>
```

#### Delete Post (Admin Only)
```http
DELETE /api/admin/posts/<post_id>
Authorization: Bearer <admin_token>
```

## 🧪 Testing

### Backend Testing

Run all backend tests:
```bash
cd backend
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_api_auth.py
```

### Frontend Testing

Run all frontend tests:
```bash
npm test
```

Run tests with UI:
```bash
npm run test:ui
```

Run tests with coverage:
```bash
npm run test:coverage
```

### Test Coverage

The project includes comprehensive test coverage:
- **Backend**: 86% code coverage
- **Frontend**: 75%+ code coverage
- **Security Tests**: 100% coverage for security components

## 🔒 Security

### Security Features

The application implements multiple security layers:

1. **Authentication & Authorization**
   - Session-based authentication with secure tokens
   - Role-based access control (RBAC)
   - Database-verified role authorization

2. **Input Validation**
   - Comprehensive input validation and sanitization
   - SQL injection prevention
   - XSS protection

3. **File Upload Security**
   - File type validation
   - File signature verification
   - Path traversal prevention
   - File size limits

4. **CSRF Protection**
   - Token-based CSRF prevention
   - SameSite cookie attributes

5. **Password Security**
   - Argon2 password hashing
   - Secure password storage

6. **Session Security**
   - HttpOnly cookies
   - Secure cookie attributes
   - Session token expiration
   - Automatic token refresh

### Security Documentation

For detailed security information, see:
- [ACCESS_CONTROL_REPORT.md](./ACCESS_CONTROL_REPORT.md) - Access control implementation
- [SESSION_MANAGEMENT.md](./SESSION_MANAGEMENT.md) - Session management details
- [OWASP_PROACTIVE_CONTROLS.md](./OWASP_PROACTIVE_CONTROLS.md) - OWASP compliance

## 📁 Project Structure

```
FeedFinder/
├── backend/                 # Backend Flask application
│   ├── app/
│   │   ├── __init__.py     # Flask app initialization
│   │   ├── auth_middleware.py  # Authentication middleware
│   │   ├── csrf.py         # CSRF protection
│   │   ├── db.py           # Database connection
│   │   ├── hash.py         # Password hashing
│   │   ├── routes.py       # API routes
│   │   ├── session_manager.py  # Session management
│   │   └── file_validator.py   # File validation
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── pytest.ini         # Pytest configuration
├── src/                    # Frontend React application
│   ├── components/         # React components
│   │   ├── AdminPage.jsx   # Admin panel
│   │   ├── FeedFinder.jsx  # Main application
│   │   ├── LoginModal.jsx  # Login component
│   │   ├── PostCards.jsx   # Post display
│   │   └── ...
│   ├── authService.js      # Authentication service
│   ├── config.js           # Configuration
│   └── test/               # Frontend tests
├── sql_stuff/              # Database files
│   ├── latestsqlvol.sql   # Database schema
│   └── docker-compose.yml  # Docker configuration
├── public/                 # Static files
├── package.json           # Node.js dependencies
├── vite.config.js         # Vite configuration
└── tailwind.config.js     # Tailwind configuration
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=feedfinder
SECRET_KEY=your_secret_key
```

#### Frontend (.env)
```env
VITE_API_BASE=http://localhost:5000
```

### Database Configuration

The application uses MySQL as the database. Ensure you have:
1. MySQL server running
2. Database created (`feedfinder`)
3. User with appropriate permissions
4. Schema imported from `sql_stuff/latestsqlvol.sql`

## 🚧 Development

### Running in Development Mode

1. **Backend**:
```bash
cd backend
export FLASK_ENV=development
python -m flask run --port=5000 --debug
```

2. **Frontend**:
```bash
npm run dev
```

### Building for Production

1. **Frontend**:
```bash
npm run build
```

2. **Backend**:
```bash
# Use a production WSGI server like Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 Scripts

### Available NPM Scripts

```bash
npm run dev              # Start development server
npm run build            # Build for production
npm run preview          # Preview production build
npm test                 # Run tests
npm run test:ui          # Run tests with UI
npm run test:coverage    # Run tests with coverage
npm run check:deps       # Check frontend dependencies
npm run check:deps:backend  # Check backend dependencies
npm run check:deps:all   # Check all dependencies
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 📊 Testing Reports

For detailed testing information, see:
- [TESTING_REPORT.md](./TESTING_REPORT.md) - Comprehensive testing report
- [TESTING_REPORT_SUMMARY.md](./TESTING_REPORT_SUMMARY.md) - Testing summary

## 🐛 Known Issues

- Some features are still under development
- Admin panel requires manual role assignment in database
- File upload size limits may need adjustment for production

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OWASP** - Security best practices and guidelines
- **React** - UI library
- **Flask** - Web framework
- **Tailwind CSS** - CSS framework
- **Lucide** - Icon library

## 📞 Support

For support, please open an issue in the repository or contact the development team.

## 🔗 Related Documentation

- [ACCESS_CONTROL_REPORT.md](./ACCESS_CONTROL_REPORT.md) - Access control implementation
- [SESSION_MANAGEMENT.md](./SESSION_MANAGEMENT.md) - Session management
- [OWASP_PROACTIVE_CONTROLS.md](./OWASP_PROACTIVE_CONTROLS.md) - OWASP compliance
- [TESTING_REPORT.md](./TESTING_REPORT.md) - Testing documentation
- [DEPENDENCY_CHECKS.md](./DEPENDENCY_CHECKS.md) - Dependency information

---

<div align="center">

**Made with ❤️ by the FeedFinder Team**

[Report Bug](https://github.com/your-repo/issues) • [Request Feature](https://github.com/your-repo/issues) • [Documentation](./docs)

</div>
