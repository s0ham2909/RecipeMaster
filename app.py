import os
import uuid
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from jose import jwt, JWTError
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
COGNITO_CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'recipes')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# AWS Clients
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Get Cognito JWKs for token validation
COGNITO_JWKS_URL = f'https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
jwks = requests.get(COGNITO_JWKS_URL).json()

# ==================== Helper Functions ====================

def get_cognito_public_key(token):
    """Extract and return the public key from Cognito JWKS"""
    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']
    
    # Find the key in JWKS
    for key in jwks['keys']:
        if key['kid'] == kid:
            return key
    
    raise ValueError('Public key not found in JWKS')

def verify_cognito_token(token):
    """Verify and decode Cognito JWT token"""
    try:
        # Get the public key
        public_key = get_cognito_public_key(token)
        
        # Decode and verify the token
        claims = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=COGNITO_CLIENT_ID,
            issuer=f'https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        )
        
        return claims
    except JWTError as e:
        raise ValueError(f'Token validation failed: {str(e)}')

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Verify and decode the token
            current_user = verify_cognito_token(token)
            request.current_user = current_user
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def upload_to_s3(file, filename):
    """Upload file to S3 and return the public URL"""
    try:
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Upload file to S3
        s3_client.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )
        
        # Generate public URL
        url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        return url
    except Exception as e:
        raise Exception(f'S3 upload failed: {str(e)}')

# ==================== Authentication Routes ====================

@app.route('/signup', methods=['POST'])
def signup():
    """User signup endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Create user in Cognito
        response = cognito_client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name}
            ]
        )
        
        return jsonify({
            'message': 'User created successfully. Please check your email for confirmation code.',
            'userSub': response['UserSub']
        }), 201
        
    except ClientError as e:
        return jsonify({'error': e.response['Error']['Message']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/confirm', methods=['POST'])
def confirm():
    """Email confirmation endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'error': 'Email and confirmation code are required'}), 400
        
        # Confirm user signup
        cognito_client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=code
        )
        
        return jsonify({'message': 'Email confirmed successfully'}), 200
        
    except ClientError as e:
        return jsonify({'error': e.response['Error']['Message']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        return jsonify({
            'message': 'Login successful',
            'accessToken': response['AuthenticationResult']['AccessToken'],
            'idToken': response['AuthenticationResult']['IdToken'],
            'refreshToken': response['AuthenticationResult']['RefreshToken']
        }), 200
        
    except ClientError as e:
        return jsonify({'error': e.response['Error']['Message']}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Recipe Routes ====================

@app.route('/recipes', methods=['POST'])
@token_required
def create_recipe():
    """Create a new recipe with image upload"""
    try:
        # Get user ID from token
        user_id = request.current_user['sub']
        
        # Get form data
        title = request.form.get('title')
        ingredients = request.form.get('ingredients')
        instructions = request.form.get('instructions')
        
        if not title or not ingredients or not instructions:
            return jsonify({'error': 'Title, ingredients, and instructions are required'}), 400
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_url = upload_to_s3(file, file.filename)
        
        # Create recipe item
        recipe_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'recipeId': recipe_id,
            'userId': user_id,
            'title': title,
            'ingredients': ingredients,
            'instructions': instructions,
            'imageUrl': image_url,
            'createdAt': timestamp,
            'updatedAt': timestamp
        }
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        return jsonify({
            'message': 'Recipe created successfully',
            'recipe': item
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes (public endpoint)"""
    try:
        # Scan all recipes
        response = table.scan()
        recipes = response.get('Items', [])
        
        return jsonify({'recipes': recipes}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a single recipe by ID (public endpoint)"""
    try:
        # Get recipe from DynamoDB
        response = table.get_item(Key={'recipeId': recipe_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Recipe not found'}), 404
        
        return jsonify({'recipe': response['Item']}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recipes/<recipe_id>', methods=['PUT'])
@token_required
def update_recipe(recipe_id):
    """Update a recipe (protected endpoint)"""
    try:
        user_id = request.current_user['sub']
        
        # Get existing recipe
        response = table.get_item(Key={'recipeId': recipe_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Recipe not found'}), 404
        
        recipe = response['Item']
        
        # Verify ownership
        if recipe['userId'] != user_id:
            return jsonify({'error': 'Unauthorized: You can only update your own recipes'}), 403
        
        # Get form data
        title = request.form.get('title', recipe['title'])
        ingredients = request.form.get('ingredients', recipe['ingredients'])
        instructions = request.form.get('instructions', recipe['instructions'])
        
        # Handle image upload if provided
        image_url = recipe.get('imageUrl')
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_url = upload_to_s3(file, file.filename)
        
        # Update recipe
        timestamp = datetime.utcnow().isoformat()
        
        table.update_item(
            Key={'recipeId': recipe_id},
            UpdateExpression='SET title = :title, ingredients = :ingredients, instructions = :instructions, imageUrl = :imageUrl, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':title': title,
                ':ingredients': ingredients,
                ':instructions': instructions,
                ':imageUrl': image_url,
                ':updatedAt': timestamp
            }
        )
        
        return jsonify({
            'message': 'Recipe updated successfully',
            'recipe': {
                'recipeId': recipe_id,
                'userId': user_id,
                'title': title,
                'ingredients': ingredients,
                'instructions': instructions,
                'imageUrl': image_url,
                'updatedAt': timestamp
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recipes/<recipe_id>', methods=['DELETE'])
@token_required
def delete_recipe(recipe_id):
    """Delete a recipe (protected endpoint)"""
    try:
        user_id = request.current_user['sub']
        
        # Get existing recipe
        response = table.get_item(Key={'recipeId': recipe_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Recipe not found'}), 404
        
        recipe = response['Item']
        
        # Verify ownership
        if recipe['userId'] != user_id:
            return jsonify({'error': 'Unauthorized: You can only delete your own recipes'}), 403
        
        # Delete recipe from DynamoDB
        table.delete_item(Key={'recipeId': recipe_id})
        
        return jsonify({'message': 'Recipe deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Health Check ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
