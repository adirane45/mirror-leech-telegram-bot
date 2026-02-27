# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 3.1.x   | :white_check_mark: |
| 3.0.x   | :white_check_mark: |
| < 3.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@yourproject.com** (or create a private issue)

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below to help us better understand the nature and scope of the possible issue:

### Information to Include

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Security Best Practices

### For Deployment

1. **Never commit sensitive data**
   - Use environment variables for secrets
   - Add `.env` to `.gitignore`
   - Review commits before pushing

2. **Keep dependencies updated**
   ```bash
   pip install -U -r requirements.txt
   ```

3. **Use secure Docker images**
   - Use official Python base images
   - Scan images for vulnerabilities
   - Update base images regularly

4. **Secure your bot token**
   - Regenerate token if exposed
   - Use strong authentication
   - Limit bot permissions

5. **Enable logging but protect sensitive data**
   - Don't log passwords or tokens
   - Sanitize user inputs in logs
   - Secure log file access

### For Configuration

1. **MongoDB Security**
   - Enable authentication
   - Use strong passwords
   - Restrict network access
   - Enable encryption at rest

2. **Redis Security**
   - Set requirepass
   - Bind to localhost only
   - Disable dangerous commands

3. **Telegram Bot Security**
   - Set webhook with valid SSL certificate
   - Validate bot token on startup
   - Implement rate limiting

### For Users

1. **Authorized Users Only**
   - Configure `SUDO_USERS` list
   - Use `AUTHORIZED_CHATS` for group/channel restrictions
   - Regularly audit user access

2. **File Security**
   - Validate file types before download
   - Scan uploads for malware
   - Set download size limits

3. **Rate Limiting**
   - Configure appropriate limits per user
   - Monitor abuse patterns
   - Block suspicious users

## Known Security Considerations

### 1. Download URLs
- The bot trusts user-provided URLs. Implement URL validation and sandboxing if exposing to untrusted users.

### 2. File Execution
- Downloaded files are not automatically executed, but be cautious with extraction features.

### 3. API Rate Limits
- Respect Telegram API rate limits (circuit breakers help with this)
- Monitor for abuse patterns

### 4. Data Storage
- Credentials stored in MongoDB should be encrypted
- Session files contain auth tokens - protect data/ directory

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find similar problems
3. Prepare fixes for all supported versions
4. Release patches as soon as possible

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request.
