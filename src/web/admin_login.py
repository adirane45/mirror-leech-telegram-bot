"""Admin login page HTML"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - Mirror Leech Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 100%;
        }

        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-header h1 {
            font-size: 32px;
            color: #667eea;
            margin-bottom: 10px;
        }

        .login-header p {
            color: #7f8c8d;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #2c3e50;
            font-weight: 500;
            font-size: 14px;
        }

        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }

        .login-btn:active {
            transform: translateY(0);
        }

        .alert {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .loading {
            display: none;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 20px;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .footer {
            text-align: center;
            margin-top: 20px;
            color: #95a5a6;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🔐 Admin Login</h1>
            <p>Mirror Leech Bot Management</p>
        </div>

        <div id="alert" class="alert"></div>

        <form onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="username">Username</label>
                <input
                    type="text"
                    id="username"
                    placeholder="Enter username"
                    required
                    autocomplete="username"
                >
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input
                    type="password"
                    id="password"
                    placeholder="Enter password"
                    required
                    autocomplete="current-password"
                >
            </div>

            <button type="submit" class="login-btn">Sign In</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Logging in...</p>
        </div>

        <div class="footer">
            <p>Default credentials: admin / admin123</p>
            <p style="margin-top: 10px; font-size: 11px; color: #bdc3c7;">⚠️ Change password in production!</p>
        </div>
    </div>

    <script>
        async function handleLogin(event) {
            event.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const alertDiv = document.getElementById('alert');
            const loadingDiv = document.getElementById('loading');

            // Show loading
            loadingDiv.style.display = 'block';

            try {
                const response = await fetch('/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });

                if (response.ok) {
                    const data = await response.json();

                    // Store token
                    localStorage.setItem('auth_token', data.access_token);

                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/admin/dashboard';
                    }, 500);
                } else {
                    const error = await response.json();
                    showAlert(error.detail || 'Login failed', 'error', alertDiv);
                    loadingDiv.style.display = 'none';
                }
            } catch (error) {
                showAlert('Error: ' + error.message, 'error', alertDiv);
                loadingDiv.style.display = 'none';
            }
        }

        function showAlert(message, type, container) {
            container.className = `alert alert-${type}`;
            container.textContent = message;
            container.style.display = 'block';
        }

        // Check if already logged in
        window.addEventListener('load', () => {
            const token = localStorage.getItem('auth_token');
            if (token) {
                window.location.href = '/admin/dashboard';
            }
        });
    </script>
</body>
</html>
"""

def get_login_html() -> str:
    return LOGIN_HTML
