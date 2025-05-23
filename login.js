// DOM Elements
const container = document.getElementById('container');
const loginBtn = document.querySelector('.login-btn');
const registerBtn = document.querySelector('.register-btn');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const registerButton = document.getElementById('registerBtn');
const loginUsername = document.getElementById('loginUsername');
const loginPassword = document.getElementById('loginPassword');
const registerUsername = document.getElementById('registerUsername');
const registerEmail = document.getElementById('registerEmail');
const registerPassword = document.getElementById('registerPassword');
const forgotPassword = document.getElementById('forgotPassword');

// Check if user is already logged in
function checkAuth() {
    const loggedInUser = localStorage.getItem('currentUser');
    if (loggedInUser) {
        window.location.href = 'dashboard.html';
    }
}

// Load users from localStorage or create initial data
function loadUsers() {
    const storedUsers = localStorage.getItem('users');
    if (storedUsers) {
        return JSON.parse(storedUsers);
    } else {
        // Create initial admin user if no users exist
        const initialUsers = [
            {
                username: 'admin',
                email: 'admin@example.com',
                password: 'admin123'
            }
        ];
        localStorage.setItem('users', JSON.stringify(initialUsers));
        return initialUsers;
    }
}

// Wechsel zwischen Login und Registrierung
loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
});

registerBtn.addEventListener('click', () => {
    container.classList.add('active');
});

// Login Handling
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const username = loginUsername.value;
    const password = loginPassword.value;
    
    if (!username || !password) {
        alert('Bitte gib deinen Benutzernamen und dein Passwort ein');
        return;
    }
    
    // Get users from localStorage
    const users = loadUsers();
    
    // Find user
    const user = users.find(user => 
        user.username === username && 
        user.password === password
    );
    
    if (user) {
        // Store logged in user in localStorage
        localStorage.setItem('currentUser', JSON.stringify(user));
        
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } else {
        alert('Ungültiger Benutzername oder Passwort');
    }
});

// Registration Handling
registerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const username = registerUsername.value;
    const email = registerEmail.value;
    const password = registerPassword.value;
    
    if (!username || !email || !password) {
        alert('Bitte fülle alle Felder aus');
        return;
    }
    
    // Get users from localStorage
    const users = loadUsers();
    
    // Check if username already exists
    if (users.some(user => user.username === username)) {
        alert('Dieser Benutzername ist bereits vergeben');
        return;
    }
    
    // Check if email already exists
    if (users.some(user => user.email === email)) {
        alert('Diese E-Mail-Adresse wird bereits verwendet');
        return;
    }
    
    // Create new user
    const newUser = {
        username,
        email,
        password
    };
    
    // Add new user to users array
    users.push(newUser);
    
    // Save users to localStorage
    localStorage.setItem('users', JSON.stringify(users));
    
    // Erfolg! Button grün machen und Text ändern
    registerButton.textContent = "Erfolgreich";
    registerButton.classList.add('btn-success');
    registerButton.disabled = true;
    
    // Nach 1.5 Sekunden zurücksetzen und zum Login wechseln
    setTimeout(() => {
        // Formular zurücksetzen
        registerForm.reset();
        
        // Button zurücksetzen
        registerButton.textContent = "Registrieren";
        registerButton.classList.remove('btn-success');
        registerButton.disabled = false;
        
        // Zur Login-Ansicht wechseln
        container.classList.remove('active');
        
        // Benutzername ins Login-Formular übertragen
        loginUsername.value = username;
        
        alert('Registrierung erfolgreich! Du kannst dich jetzt anmelden.');
    }, 1500);
});

// Forgot Password Handling
forgotPassword.addEventListener('click', (e) => {
    e.preventDefault();
    
    const username = prompt('Bitte gib deinen Benutzernamen ein:');
    
    if (!username) {
        return;
    }
    
    // Get users from localStorage
    const users = loadUsers();
    
    // Find user
    const user = users.find(user => user.username === username);
    
    if (user) {
        alert(`Passwort-zurücksetzen-Funktion für ${username} nicht verfügbar. (Demo-Modus)`);
    } else {
        alert('Benutzer nicht gefunden');
    }
});

// Check authentication on page load
checkAuth(); 