// DOM Elements
const sidebar = document.querySelector('.sidebar');
const collapseBtn = document.getElementById('collapseBtn');
const logoutBtn = document.getElementById('logoutBtn');
const navItems = document.querySelectorAll('.nav-item');
const pageContents = document.querySelectorAll('.page-content');
const userSelect = document.getElementById('userSelect');
const userEmail = document.getElementById('userEmail');
const keyGeneratorForm = document.getElementById('keyGeneratorForm');
const generatedKeyDisplay = document.getElementById('generatedKeyDisplay');
const copyKeyBtn = document.getElementById('copyKeyBtn');
const searchKeys = document.getElementById('searchKeys');
const keyFilter = document.getElementById('keyFilter');
const keysTable = document.getElementById('keysTable');
const recentKeysTable = document.getElementById('recentKeysTable');
const profileSettingsForm = document.getElementById('profileSettingsForm');
const profileUsername = document.getElementById('profileUsername');
const profileEmail = document.getElementById('profileEmail');
const profilePassword = document.getElementById('profilePassword');
const downloadTriggerBtn = document.getElementById('downloadTriggerBtn');
const darkModeToggle = document.getElementById('darkModeToggle');
const notificationsToggle = document.getElementById('notificationsToggle');
const autoLogoutToggle = document.getElementById('autoLogoutToggle');
const viewAllBtn = document.querySelector('.view-all-btn');
const usernames = document.querySelectorAll('.username');
const keyCount = document.getElementById('keyCount');
const userCount = document.getElementById('userCount');
const downloadCount = document.getElementById('downloadCount');
const tabBtns = document.querySelectorAll('.tab-btn');
const adminTabContents = document.querySelectorAll('.admin-tab-content');
const searchUsers = document.getElementById('searchUsers');
const searchAdminKeys = document.getElementById('searchAdminKeys');
const adminKeyFilter = document.getElementById('adminKeyFilter');
const usersTable = document.getElementById('usersTable');
const adminKeysTable = document.getElementById('adminKeysTable');
const adminNavItem = document.getElementById('adminNavItem');

// Data Storage
let currentUser = null;
let users = [];
let keys = [];

// API Configuration
const API_URL = 'https://fastapi-app.onrender.com';  // Render.com API URL

// Utility Functions
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

async function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        try {
            await navigator.clipboard.writeText(element.value);
            showNotification('Copied to clipboard!');
        } catch (err) {
            showNotification('Failed to copy text', 'error');
        }
    }
}

// API Functions
async function generateKey(username, daysValid) {
    try {
        const response = await fetch(`${API_URL}/api/admin/generate_key`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                days_valid: parseInt(daysValid)
            })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail?.message || 'Failed to generate key');
        }
        
        return data;
    } catch (error) {
        showNotification(error.message, 'error');
        return null;
    }
}

async function fetchRecentKeys() {
    try {
        const response = await fetch(`${API_URL}/api/admin/list_keys`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail?.message || 'Failed to fetch keys');
        }
        
        return data.licenses;
    } catch (error) {
        showNotification(error.message, 'error');
        return [];
    }
}

async function resetHWID(key) {
    try {
        const response = await fetch(`${API_URL}/api/admin/reset_hwid`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ key })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail?.message || 'Failed to reset HWID');
        }
        
        showNotification('HWID reset successfully');
        return true;
    } catch (error) {
        showNotification(error.message, 'error');
        return false;
    }
}

// Check if user is logged in
function checkAuth() {
    const loggedInUser = localStorage.getItem('currentUser');
    if (!loggedInUser) {
        window.location.href = 'index.html';
        return;
    }
    
    currentUser = JSON.parse(loggedInUser);
    loadData();
    updateUI();
}

// Load data from localStorage or create initial data
function loadData() {
    // Load Users
    const storedUsers = localStorage.getItem('users');
    if (storedUsers) {
        users = JSON.parse(storedUsers);
    } else {
        // Sample user data if none exists
        users = [
            {
                username: 'admin',
                email: 'admin@example.com',
                password: 'admin123'
            }
        ];
        localStorage.setItem('users', JSON.stringify(users));
    }
    
    // Load Keys
    const storedKeys = localStorage.getItem('keys');
    if (storedKeys) {
        keys = JSON.parse(storedKeys);
    } else {
        // Sample key data if none exists
        keys = [];
        localStorage.setItem('keys', JSON.stringify(keys));
    }
    
    // Hide admin nav item for non-admin users
    if (currentUser && currentUser.username === 'admin') {
        adminNavItem.style.display = 'list-item';
    } else {
        adminNavItem.style.display = 'none';
    }
}

// Update UI elements with current data
function updateUI() {
    // Update username displays
    usernames.forEach(element => {
        element.textContent = currentUser.username;
    });
    
    // Update dashboard counts
    keyCount.textContent = keys.length;
    userCount.textContent = users.length;
    downloadCount.textContent = localStorage.getItem('downloadCount') || '0';
    
    // Populate user select dropdown
    populateUserSelect();
    
    // Update keys tables
    renderKeysTable();
    renderRecentKeysTable();
    
    // Update profile settings form
    profileUsername.value = currentUser.username;
    profileEmail.value = currentUser.email;
}

// Populate user select in key generator
function populateUserSelect() {
    userSelect.innerHTML = '<option value="">Benutzer auswählen</option>';
    users.forEach(user => {
        const option = document.createElement('option');
        option.value = user.username;
        option.textContent = user.username;
        userSelect.appendChild(option);
    });
}

// Toggle sidebar collapse
collapseBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
});

// Navigation between pages
navItems.forEach(item => {
    item.addEventListener('click', () => {
        const targetPage = item.getAttribute('data-page');
        
        // Update active nav item
        navItems.forEach(navItem => navItem.classList.remove('active'));
        item.classList.add('active');
        
        // Update page title
        document.querySelector('.page-title h1').textContent = item.querySelector('span').textContent;
        
        // Show target page
        pageContents.forEach(page => page.classList.remove('active'));
        document.getElementById(`${targetPage}-page`).classList.add('active');
    });
});

// View all keys button
viewAllBtn.addEventListener('click', () => {
    const targetPage = viewAllBtn.getAttribute('data-page');
    
    // Update active nav item
    navItems.forEach(navItem => {
        if (navItem.getAttribute('data-page') === targetPage) {
            navItem.classList.add('active');
        } else {
            navItem.classList.remove('active');
        }
    });
    
    // Update page title
    document.querySelector('.page-title h1').textContent = 'Users & Keys';
    
    // Show target page
    pageContents.forEach(page => page.classList.remove('active'));
    document.getElementById(`${targetPage}-page`).classList.add('active');
});

// User select change
userSelect.addEventListener('change', () => {
    const selectedUser = users.find(user => user.username === userSelect.value);
    if (selectedUser) {
        userEmail.value = selectedUser.email;
    } else {
        userEmail.value = '';
    }
});

// Generate key
keyGeneratorForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const validityDays = document.getElementById('validityDays').value;
    
    if (!username) {
        showNotification('Please enter a username', 'error');
        return;
    }
    
    const result = await generateKey(username, validityDays);
    if (result) {
        document.getElementById('generatedKey').value = result.license.key;
        document.getElementById('generatedKeyContainer').style.display = 'block';
        
        // Add to recent keys table
        if (recentKeysTable) {
            const row = document.createElement('tr');
            const expiryDate = result.license.valid_until ? 
                new Date(result.license.valid_until).toLocaleDateString() : 
                'Never';
            
            row.innerHTML = `
                <td>${result.license.username}</td>
                <td>${result.license.key}</td>
                <td>${result.license.hwid || 'Not registered'}</td>
                <td>${new Date(result.license.created_at).toLocaleDateString()}</td>
                <td>${expiryDate}</td>
                <td>
                    <button class="action-btn copy-key-btn" onclick="copyToClipboard('${result.license.key}')">
                        <i class='bx bx-copy'></i>
                    </button>
                    <button class="action-btn reset-hwid-btn" onclick="resetHWID('${result.license.key}')">
                        <i class='bx bx-reset'></i>
                    </button>
                </td>
            `;
            recentKeysTable.insertBefore(row, recentKeysTable.firstChild);
        }
        
        showNotification('Key generated successfully');
    }
});

// Check for expired keys and clean them
function cleanExpiredKeys() {
    const now = new Date();
    const validKeys = keys.filter(key => {
        if (!key.expires_at) return true;
        return new Date(key.expires_at) > now;
    });
    
    if (validKeys.length < keys.length) {
        keys = validKeys;
        localStorage.setItem('keys', JSON.stringify(keys));
        keyCount.textContent = keys.length;
    }
}

// Format date and time for display
function formatDateTime(date) {
    const d = new Date(date);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
}

// Format expiration for display
function formatExpiration(expiresAt) {
    if (!expiresAt) return "Nie";
    
    const now = new Date();
    const expiry = new Date(expiresAt);
    
    if (expiry < now) {
        return "Abgelaufen";
    }
    
    // Calculate remaining time
    const diffMs = expiry - now;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 60) {
        return `In ${diffMins} min`;
    }
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
        return `In ${diffHours} std`;
    }
    
    const diffDays = Math.floor(diffHours / 24);
    return `In ${diffDays} tagen`;
}

// Copy key to clipboard
copyKeyBtn.addEventListener('click', () => {
    const keyText = document.querySelector('.key-text');
    if (keyText) {
        navigator.clipboard.writeText(keyText.textContent)
            .then(() => {
                const originalText = copyKeyBtn.innerHTML;
                copyKeyBtn.innerHTML = '<i class="bx bx-check"></i> Kopiert';
                setTimeout(() => {
                    copyKeyBtn.innerHTML = originalText;
                }, 2000);
            })
            .catch(err => {
                alert('Fehler beim Kopieren: ' + err);
            });
    }
});

// Search and filter keys
searchKeys.addEventListener('input', filterKeys);
keyFilter.addEventListener('change', filterKeys);

function filterKeys() {
    const searchTerm = searchKeys.value.toLowerCase();
    const filterOption = keyFilter.value;
    
    const filteredKeys = keys.filter(key => {
        if (filterOption === 'username') {
            return key.username.toLowerCase().includes(searchTerm);
        } else if (filterOption === 'email') {
            return key.email.toLowerCase().includes(searchTerm);
        } else {
            return (
                key.username.toLowerCase().includes(searchTerm) ||
                key.email.toLowerCase().includes(searchTerm) ||
                key.key.toLowerCase().includes(searchTerm)
            );
        }
    });
    
    renderKeysTable(filteredKeys);
}

// Render keys table
function renderKeysTable(keysToRender = keys) {
    keysTable.innerHTML = '';
    cleanExpiredKeys();
    
    if (keysToRender.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="7">Keine Keys gefunden</td>`;
        keysTable.appendChild(row);
        return;
    }
    
    keysToRender.forEach(key => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${key.username}</td>
            <td>${key.email}</td>
            <td>${key.key}</td>
            <td>${key.hwid}</td>
            <td>${key.created_at}</td>
            <td>${formatExpiration(key.expires_at)}</td>
            <td>
                <button class="action-btn copy-key-btn" data-key="${key.key}">
                    <i class='bx bx-copy'></i>
                </button>
            </td>
        `;
        keysTable.appendChild(row);
    });
    
    // Add event listeners to copy buttons
    document.querySelectorAll('.copy-key-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const keyToCopy = btn.getAttribute('data-key');
            navigator.clipboard.writeText(keyToCopy)
                .then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '<i class="bx bx-check"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                    }, 2000);
                })
                .catch(err => {
                    alert('Fehler beim Kopieren: ' + err);
                });
        });
    });
}

// Render recent keys table
function renderRecentKeysTable() {
    recentKeysTable.innerHTML = '';
    cleanExpiredKeys();
    
    // Get 5 most recent keys
    const recentKeys = [...keys].sort((a, b) => {
        return new Date(b.created_at) - new Date(a.created_at);
    }).slice(0, 5);
    
    if (recentKeys.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6">Keine Keys gefunden</td>`;
        recentKeysTable.appendChild(row);
        return;
    }
    
    recentKeys.forEach(key => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${key.username}</td>
            <td>${key.key}</td>
            <td>${key.hwid}</td>
            <td>${key.created_at}</td>
            <td>${formatExpiration(key.expires_at)}</td>
            <td>
                <button class="action-btn copy-recent-key-btn" data-key="${key.key}">
                    <i class='bx bx-copy'></i>
                </button>
            </td>
        `;
        recentKeysTable.appendChild(row);
    });
    
    // Add event listeners to copy buttons
    document.querySelectorAll('.copy-recent-key-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const keyToCopy = btn.getAttribute('data-key');
            navigator.clipboard.writeText(keyToCopy)
                .then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '<i class="bx bx-check"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                    }, 2000);
                })
                .catch(err => {
                    alert('Fehler beim Kopieren: ' + err);
                });
        });
    });
}

// Add an automatic check for expired keys every minute
setInterval(function() {
    if (keys.length > 0) {
        const oldCount = keys.length;
        cleanExpiredKeys();
        if (oldCount !== keys.length) {
            renderKeysTable();
            renderRecentKeysTable();
        }
    }
}, 60000); // Check every minute

// Save profile settings
profileSettingsForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const username = profileUsername.value;
    const email = profileEmail.value;
    const password = profilePassword.value;
    
    if (!username || !email) {
        alert('Bitte Username und Email ausfüllen');
        return;
    }
    
    // Update user data
    const userIndex = users.findIndex(user => user.username === currentUser.username);
    if (userIndex !== -1) {
        users[userIndex].username = username;
        users[userIndex].email = email;
        
        if (password) {
            users[userIndex].password = password;
        }
        
        // Update current user
        currentUser = {
            ...currentUser,
            username,
            email,
            password: password ? password : currentUser.password
        };
        
        // Update localStorage
        localStorage.setItem('users', JSON.stringify(users));
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        // Update UI
        updateUI();
        
        alert('Profil erfolgreich aktualisiert');
        profilePassword.value = '';
    }
});

// Download trigger
downloadTriggerBtn.addEventListener('click', () => {
    // In a real application, this would trigger an actual download
    // For this demo, we'll just increment the download count
    const currentDownloads = parseInt(localStorage.getItem('downloadCount') || '0');
    localStorage.setItem('downloadCount', (currentDownloads + 1).toString());
    downloadCount.textContent = (currentDownloads + 1).toString();
    
    alert('Download gestartet... (Demo: Die Datei wird nicht wirklich heruntergeladen)');
});

// Logout
logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
});

// Helper function to generate random string
function generateRandomString(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// Admin tabs switching
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        
        // Update active tab button
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show target tab content
        adminTabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        // Refresh tables when switching to tabs
        if (tabId === 'users-tab') {
            renderUsersTable();
        } else if (tabId === 'keys-tab') {
            renderAdminKeysTable();
        }
    });
});

// Search and filter users
searchUsers.addEventListener('input', filterUsers);

function filterUsers() {
    const searchTerm = searchUsers.value.toLowerCase();
    
    const filteredUsers = users.filter(user => {
        return (
            user.username.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm)
        );
    });
    
    renderUsersTable(filteredUsers);
}

// Render users table for admin
function renderUsersTable(usersToRender = users) {
    usersTable.innerHTML = '';
    
    if (usersToRender.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6">Keine Benutzer gefunden</td>`;
        usersTable.appendChild(row);
        return;
    }
    
    usersToRender.forEach(user => {
        // Count user's keys
        const userKeys = keys.filter(key => key.username === user.username);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.password}</td>
            <td>${user.created_at || 'Unbekannt'}</td>
            <td>${userKeys.length}</td>
            <td class="action-btn-group">
                <button class="action-btn view-keys-btn" data-username="${user.username}" title="Keys anzeigen">
                    <i class="bx bx-key"></i>
                </button>
                <button class="action-btn delete-btn" data-username="${user.username}" title="Benutzer löschen">
                    <i class="bx bx-trash"></i>
                </button>
            </td>
        `;
        usersTable.appendChild(row);
    });
    
    // Add event listeners to action buttons
    document.querySelectorAll('.view-keys-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const username = btn.getAttribute('data-username');
            
            // Switch to keys tab and filter by username
            tabBtns.forEach(b => {
                if (b.getAttribute('data-tab') === 'keys-tab') {
                    b.click();
                }
            });
            
            searchAdminKeys.value = username;
            filterAdminKeys();
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const username = btn.getAttribute('data-username');
            if (username === 'admin') {
                alert('Der Administrator-Account kann nicht gelöscht werden.');
                return;
            }
            
            if (confirm(`Möchten Sie den Benutzer "${username}" wirklich löschen? Alle zugehörigen Keys werden ebenfalls gelöscht.`)) {
                deleteUser(username);
            }
        });
    });
}

// Delete a user and their associated keys
function deleteUser(username) {
    // Remove user from users array
    const userIndex = users.findIndex(user => user.username === username);
    if (userIndex !== -1) {
        users.splice(userIndex, 1);
        localStorage.setItem('users', JSON.stringify(users));
        
        // Remove all keys associated with the user
        keys = keys.filter(key => key.username !== username);
        localStorage.setItem('keys', JSON.stringify(keys));
        
        // Update UI
        renderUsersTable();
        renderAdminKeysTable();
        userCount.textContent = users.length;
        keyCount.textContent = keys.length;
        
        alert(`Benutzer "${username}" wurde erfolgreich gelöscht.`);
    }
}

// Search and filter admin keys
searchAdminKeys.addEventListener('input', filterAdminKeys);
adminKeyFilter.addEventListener('change', filterAdminKeys);

function filterAdminKeys() {
    const searchTerm = searchAdminKeys.value.toLowerCase();
    const filterOption = adminKeyFilter.value;
    const now = new Date();
    
    const filteredKeys = keys.filter(key => {
        // Apply text search filter
        const textMatch = 
            key.username.toLowerCase().includes(searchTerm) ||
            key.email.toLowerCase().includes(searchTerm) ||
            key.key.toLowerCase().includes(searchTerm);
        
        if (!textMatch) return false;
        
        // Apply status filter
        if (filterOption === 'active') {
            if (!key.expires_at) return true;
            return new Date(key.expires_at) > now;
        } else if (filterOption === 'expired') {
            if (!key.expires_at) return false;
            return new Date(key.expires_at) <= now;
        }
        
        // Show all
        return true;
    });
    
    renderAdminKeysTable(filteredKeys);
}

// Render admin keys table
function renderAdminKeysTable(keysToRender = keys) {
    adminKeysTable.innerHTML = '';
    
    if (keysToRender.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="8">Keine Keys gefunden</td>`;
        adminKeysTable.appendChild(row);
        return;
    }
    
    const now = new Date();
    
    keysToRender.forEach(key => {
        // Determine key status
        let status = 'Aktiv';
        let statusClass = 'active-status';
        
        if (key.expires_at) {
            const expiryDate = new Date(key.expires_at);
            if (expiryDate <= now) {
                status = 'Abgelaufen';
                statusClass = 'expired-status';
            }
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${key.username}</td>
            <td>${key.email}</td>
            <td>${key.key}</td>
            <td>${key.hwid}</td>
            <td>${key.created_at}</td>
            <td>${formatExpiration(key.expires_at)}</td>
            <td class="${statusClass}">${status}</td>
            <td class="action-btn-group">
                <button class="action-btn copy-admin-key-btn" data-key="${key.key}" title="Key kopieren">
                    <i class="bx bx-copy"></i>
                </button>
                <button class="action-btn delete-btn delete-key-btn" data-key="${key.key}" title="Key löschen">
                    <i class="bx bx-trash"></i>
                </button>
            </td>
        `;
        adminKeysTable.appendChild(row);
    });
    
    // Add event listeners to action buttons
    document.querySelectorAll('.copy-admin-key-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const keyToCopy = btn.getAttribute('data-key');
            navigator.clipboard.writeText(keyToCopy)
                .then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '<i class="bx bx-check"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                    }, 2000);
                })
                .catch(err => {
                    alert('Fehler beim Kopieren: ' + err);
                });
        });
    });
    
    document.querySelectorAll('.delete-key-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const keyToDelete = btn.getAttribute('data-key');
            if (confirm(`Möchten Sie den Key "${keyToDelete}" wirklich löschen?`)) {
                deleteKey(keyToDelete);
            }
        });
    });
}

// Delete a specific key
function deleteKey(keyToDelete) {
    const keyIndex = keys.findIndex(key => key.key === keyToDelete);
    if (keyIndex !== -1) {
        keys.splice(keyIndex, 1);
        localStorage.setItem('keys', JSON.stringify(keys));
        
        // Update UI
        renderAdminKeysTable();
        renderKeysTable();
        renderRecentKeysTable();
        keyCount.textContent = keys.length;
        
        alert(`Key "${keyToDelete}" wurde erfolgreich gelöscht.`);
    }
}

// Add created_at field to users if not present
function updateUserData() {
    let updated = false;
    
    users.forEach(user => {
        if (!user.created_at) {
            user.created_at = new Date().toISOString().split('T')[0];
            updated = true;
        }
    });
    
    if (updated) {
        localStorage.setItem('users', JSON.stringify(users));
    }
}

// Initialize admin area when the admin page is opened
navItems.forEach(item => {
    item.addEventListener('click', () => {
        const targetPage = item.getAttribute('data-page');
        
        if (targetPage === 'admin') {
            updateUserData();
            renderUsersTable();
            renderAdminKeysTable();
        }
    });
});

// Initialize app
checkAuth(); 