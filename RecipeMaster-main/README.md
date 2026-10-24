# Recipe Master - Full Stack Application

A complete web application for sharing and discovering recipes, built with Python Flask backend and vanilla HTML/CSS/JavaScript frontend.

## Features

- **User Authentication**: Sign up, login, and email confirmation using Amazon Cognito
- **Recipe Management**: Create, read, update, and delete recipes (CRUD operations)
- **Image Upload**: Upload recipe images to Amazon S3
- **Responsive Design**: Modern, mobile-friendly UI
- **Secure API**: JWT-based authentication for protected routes

## Technology Stack

### Backend
- Python 3.x
- Flask (Web Framework)
- Amazon Cognito (Authentication)
- Amazon DynamoDB (Database)
- Amazon S3 (File Storage)
- JWT Token Validation

### Frontend
- HTML5
- CSS3
- Vanilla JavaScript (ES6+)
- Fetch API for HTTP requests

## Project Structure

```
RecipieMaster/
├── app.py                  # Flask backend application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── index.html             # Main HTML file
├── style.css              # Stylesheet
├── script.js              # JavaScript logic
└── README.md              # This file
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- AWS Account with access to Cognito, DynamoDB, and S3
- pip (Python package manager)

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS Resources:**

   **Amazon Cognito:**
   - Create a User Pool in Amazon Cognito
   - Create an App Client (enable USER_PASSWORD_AUTH flow)
   - Note down the User Pool ID and Client ID

   **Amazon DynamoDB:**
   - Create a table named `recipes`
   - Set `recipeId` (String) as the primary key

   **Amazon S3:**
   - Create an S3 bucket for storing recipe images
   - Configure bucket policy for public read access
   - Enable CORS if needed

3. **Update the `.env` file:**
   ```env
   AWS_REGION=us-east-1
   COGNITO_USER_POOL_ID=your_user_pool_id
   COGNITO_CLIENT_ID=your_client_id
   COGNITO_CLIENT_SECRET=your_client_secret
   DYNAMODB_TABLE_NAME=recipes
   S3_BUCKET_NAME=your_bucket_name
   ```

4. **Run the Flask server:**
   ```bash
   python app.py
   ```
   The backend will run on `http://127.0.0.1:5000`

### Frontend Setup

1. **Open the frontend:**
   - Simply open `index.html` in a web browser, or
   - Use a local HTTP server:
     ```bash
     python -m http.server 8000
     ```
   - Access at `http://localhost:8000`

2. **The frontend automatically connects to the backend at `http://127.0.0.1:5000`**

## API Endpoints

### Authentication
- `POST /signup` - User registration
- `POST /confirm` - Email confirmation
- `POST /login` - User login (returns JWT token)

### Recipes (Public)
- `GET /recipes` - Get all recipes
- `GET /recipes/<recipe_id>` - Get single recipe

### Recipes (Protected - Requires JWT)
- `POST /recipes` - Create new recipe (with image upload)
- `PUT /recipes/<recipe_id>` - Update recipe (owner only)
- `DELETE /recipes/<recipe_id>` - Delete recipe (owner only)

### Health Check
- `GET /health` - Server health status

## Usage

1. **Sign Up**: Create a new account with email and password
2. **Confirm Email**: Enter the confirmation code sent to your email
3. **Login**: Sign in with your credentials
4. **Create Recipe**: Click "Create Recipe" button to add a new recipe with image
5. **Browse Recipes**: View all recipes on the main feed
6. **View Details**: Click on any recipe card to see full details

## Security Features

- JWT token validation for protected routes
- User ownership verification for update/delete operations
- Secure password handling through AWS Cognito
- CORS enabled for frontend-backend communication

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AWS_REGION` | AWS region (e.g., us-east-1) |
| `COGNITO_USER_POOL_ID` | Amazon Cognito User Pool ID |
| `COGNITO_CLIENT_ID` | Cognito App Client ID |
| `COGNITO_CLIENT_SECRET` | Cognito App Client Secret |
| `DYNAMODB_TABLE_NAME` | DynamoDB table name |
| `S3_BUCKET_NAME` | S3 bucket name for images |

## Notes

- Make sure your AWS credentials are properly configured
- The S3 bucket must allow public read access for recipe images
- Cognito User Pool must have USER_PASSWORD_AUTH flow enabled
- For production, use environment variables and secure secret management

## License

MIT License - Feel free to use this project for learning or production purposes.

## Author

Recipe Master Team
