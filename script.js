// API Configuration
const API_URL = 'http://127.0.0.1:5000';

// State Management
let currentUser = null;
let recipes = [];

// DOM Elements
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');
const createRecipeBtn = document.getElementById('createRecipeBtn');
const logoutBtn = document.getElementById('logoutBtn');

const loginModal = document.getElementById('loginModal');
const signupModal = document.getElementById('signupModal');
const confirmModal = document.getElementById('confirmModal');
const createRecipeModal = document.getElementById('createRecipeModal');

const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const confirmForm = document.getElementById('confirmForm');
const createRecipeForm = document.getElementById('createRecipeForm');

const recipesGrid = document.getElementById('recipesGrid');
const loading = document.getElementById('loading');

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    // Check if user is already logged in
    const token = localStorage.getItem('accessToken');
    if (token) {
        currentUser = { token };
        updateUIForLoggedInUser();
    }
    
    // Load recipes
    loadRecipes();
}

function setupEventListeners() {
    // Navigation buttons
    loginBtn.addEventListener('click', () => showModal('loginModal'));
    signupBtn.addEventListener('click', () => showModal('signupModal'));
    createRecipeBtn.addEventListener('click', () => showModal('createRecipeModal'));
    logoutBtn.addEventListener('click', logout);
    
    // Modal close buttons
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            hideModal(e.target.dataset.modal);
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.add('hidden');
        }
    });
    
    // Form submissions
    loginForm.addEventListener('submit', handleLogin);
    signupForm.addEventListener('submit', handleSignup);
    confirmForm.addEventListener('submit', handleConfirm);
    createRecipeForm.addEventListener('submit', handleCreateRecipe);
    
    // Switch between login and signup
    document.getElementById('switchToSignup').addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('loginModal');
        showModal('signupModal');
    });
    
    document.getElementById('switchToLogin').addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('signupModal');
        showModal('loginModal');
    });
}

// ==================== Modal Management ====================

function showModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// ==================== Alert Messages ====================

function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => alert.remove(), 5000);
}

// ==================== Authentication Functions ====================

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store tokens
            localStorage.setItem('accessToken', data.accessToken);
            localStorage.setItem('idToken', data.idToken);
            
            currentUser = { token: data.accessToken };
            
            showAlert('Login successful!', 'success');
            hideModal('loginModal');
            updateUIForLoggedInUser();
            loginForm.reset();
        } else {
            showAlert(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showAlert('An error occurred during login', 'error');
        console.error('Login error:', error);
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    
    try {
        const response = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Signup successful! Please check your email for confirmation code.', 'success');
            hideModal('signupModal');
            
            // Pre-fill email in confirmation modal
            document.getElementById('confirmEmail').value = email;
            showModal('confirmModal');
            
            signupForm.reset();
        } else {
            showAlert(data.error || 'Signup failed', 'error');
        }
    } catch (error) {
        showAlert('An error occurred during signup', 'error');
        console.error('Signup error:', error);
    }
}

async function handleConfirm(e) {
    e.preventDefault();
    
    const email = document.getElementById('confirmEmail').value;
    const code = document.getElementById('confirmCode').value;
    
    try {
        const response = await fetch(`${API_URL}/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, code })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Email confirmed successfully! You can now login.', 'success');
            hideModal('confirmModal');
            showModal('loginModal');
            confirmForm.reset();
        } else {
            showAlert(data.error || 'Confirmation failed', 'error');
        }
    } catch (error) {
        showAlert('An error occurred during confirmation', 'error');
        console.error('Confirmation error:', error);
    }
}

function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('idToken');
    currentUser = null;
    
    updateUIForLoggedOutUser();
    showAlert('Logged out successfully', 'info');
}

// ==================== UI Update Functions ====================

function updateUIForLoggedInUser() {
    loginBtn.classList.add('hidden');
    signupBtn.classList.add('hidden');
    createRecipeBtn.classList.remove('hidden');
    logoutBtn.classList.remove('hidden');
}

function updateUIForLoggedOutUser() {
    loginBtn.classList.remove('hidden');
    signupBtn.classList.remove('hidden');
    createRecipeBtn.classList.add('hidden');
    logoutBtn.classList.add('hidden');
}

// ==================== Recipe Functions ====================

async function loadRecipes() {
    loading.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/recipes`);
        const data = await response.json();
        
        if (response.ok) {
            recipes = data.recipes;
            renderRecipes(recipes);
        } else {
            showAlert('Failed to load recipes', 'error');
        }
    } catch (error) {
        showAlert('An error occurred while loading recipes', 'error');
        console.error('Load recipes error:', error);
    } finally {
        loading.classList.add('hidden');
    }
}

function renderRecipes(recipesToRender) {
    recipesGrid.innerHTML = '';
    
    if (recipesToRender.length === 0) {
        recipesGrid.innerHTML = '<p style="text-align: center; grid-column: 1/-1; padding: 3rem; color: #7f8c8d;">No recipes found. Be the first to create one!</p>';
        return;
    }
    
    recipesToRender.forEach(recipe => {
        const card = createRecipeCard(recipe);
        recipesGrid.appendChild(card);
    });
}

function createRecipeCard(recipe) {
    const card = document.createElement('div');
    card.className = 'recipe-card';
    
    const imageUrl = recipe.imageUrl || 'https://via.placeholder.com/300x200?text=No+Image';
    const ingredients = recipe.ingredients.split('\n').slice(0, 3).join(', ');
    
    card.innerHTML = `
        <img src="${imageUrl}" alt="${recipe.title}" class="recipe-image" onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
        <div class="recipe-content">
            <h3 class="recipe-title">${recipe.title}</h3>
            <p class="recipe-description">${ingredients}...</p>
            <div class="recipe-actions">
                <button class="btn btn-primary" onclick="viewRecipe('${recipe.recipeId}')">View Recipe</button>
            </div>
        </div>
    `;
    
    return card;
}

async function handleCreateRecipe(e) {
    e.preventDefault();
    
    if (!currentUser) {
        showAlert('Please login to create a recipe', 'error');
        return;
    }
    
    const title = document.getElementById('recipeTitle').value;
    const ingredients = document.getElementById('recipeIngredients').value;
    const instructions = document.getElementById('recipeInstructions').value;
    const imageFile = document.getElementById('recipeImage').files[0];
    
    // Create FormData for multipart/form-data
    const formData = new FormData();
    formData.append('title', title);
    formData.append('ingredients', ingredients);
    formData.append('instructions', instructions);
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    try {
        const token = localStorage.getItem('accessToken');
        
        const response = await fetch(`${API_URL}/recipes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Recipe created successfully!', 'success');
            hideModal('createRecipeModal');
            createRecipeForm.reset();
            loadRecipes(); // Reload recipes
        } else {
            showAlert(data.error || 'Failed to create recipe', 'error');
        }
    } catch (error) {
        showAlert('An error occurred while creating recipe', 'error');
        console.error('Create recipe error:', error);
    }
}

async function viewRecipe(recipeId) {
    try {
        const response = await fetch(`${API_URL}/recipes/${recipeId}`);
        const data = await response.json();
        
        if (response.ok) {
            displayRecipeDetail(data.recipe);
        } else {
            showAlert('Failed to load recipe details', 'error');
        }
    } catch (error) {
        showAlert('An error occurred while loading recipe details', 'error');
        console.error('View recipe error:', error);
    }
}

function displayRecipeDetail(recipe) {
    const imageUrl = recipe.imageUrl || 'https://via.placeholder.com/800x400?text=No+Image';
    
    recipesGrid.innerHTML = `
        <div class="recipe-detail" style="grid-column: 1/-1;">
            <button class="btn btn-secondary" onclick="loadRecipes()" style="margin-bottom: 1rem;">← Back to Recipes</button>
            <img src="${imageUrl}" alt="${recipe.title}" class="recipe-detail-image" onerror="this.src='https://via.placeholder.com/800x400?text=No+Image'">
            <h2>${recipe.title}</h2>
            <h3>Ingredients</h3>
            <pre>${recipe.ingredients}</pre>
            <h3>Instructions</h3>
            <pre>${recipe.instructions}</pre>
        </div>
    `;
}

// Make viewRecipe available globally
window.viewRecipe = viewRecipe;
