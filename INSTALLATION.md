# Installation Guide - Firefly III CSV Importer

This guide will walk you through installing and configuring the Firefly III CSV Importer add-on for Home Assistant.

## Prerequisites

- Home Assistant installation (version 2023.11 or later)
- Firefly III instance running and accessible from Home Assistant
- Personal Access Token from Firefly III (see below)

## Installation Methods

### Method 1: Manual Installation (Recommended for Development)

1. **SSH into your Home Assistant system:**
   ```bash
   ssh root@homeassistant.local
   # or use your Home Assistant IP address
   ```

2. **Navigate to the add-ons directory:**
   ```bash
   cd /addons
   ```

3. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/firefly-csv-importer.git
   cd firefly-csv-importer
   ```

4. **Restart Home Assistant:**
   - Settings → System → Supervisor → Restart

5. **Check the add-on store:**
   - Settings → Add-ons & Integrations → Add-ons
   - You should see "Firefly III CSV Importer" in the list

### Method 2: Using Docker (For Testing)

1. **Build the Docker image:**
   ```bash
   docker build -t firefly-csv-importer .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8099:8099 \
     -e FIREFLY_BASE_URL=http://firefly:8080 \
     -e FIREFLY_TOKEN=your_token_here \
     -v /tmp/firefly_uploads:/tmp/firefly_uploads \
     firefly-csv-importer
   ```

3. **Access the UI:**
   - Open `http://localhost:8099` in your browser

### Method 3: Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  firefly-importer:
    build: .
    container_name: firefly-csv-importer
    ports:
      - "8099:8099"
    environment:
      FIREFLY_BASE_URL: http://firefly:8080
      FIREFLY_TOKEN: ${FIREFLY_TOKEN}
      PORT: 8099
      PYTHONUNBUFFERED: 1
    volumes:
      - /tmp/firefly_uploads:/tmp/firefly_uploads
    restart: unless-stopped
    depends_on:
      - firefly

  firefly:
    image: jc5x/firefly-iii:latest
    container_name: firefly-iii
    ports:
      - "8080:8080"
    environment:
      APP_KEY: ${APP_KEY}
      DB_HOST: db
      DB_PASSWORD: ${DB_PASSWORD}
      DB_USERNAME: firefly
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: mariadb:latest
    container_name: firefly-db
    environment:
      MYSQL_DATABASE: firefly
      MYSQL_USER: firefly
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
    volumes:
      - firefly_db_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  firefly_db_data:
```

Run with:
```bash
export FIREFLY_TOKEN=your_token_here
export APP_KEY=base64:your_app_key
export DB_PASSWORD=your_db_password
docker-compose up -d
```

## Firefly III Configuration

### Getting Your Personal Access Token

1. **Open Firefly III:**
   - Navigate to your Firefly III instance in a browser
   - Log in with your credentials

2. **Go to Settings:**
   - Click on your user profile (top-right corner)
   - Select "Profile"

3. **Create a Personal Access Token:**
   - Scroll down to "Personal Access Tokens" section
   - Click "Create New Token"
   - Enter a name: `HomeAssistant CSV Importer`
   - Click "Generate"
   - **Important:** Copy the token immediately and save it somewhere safe

4. **Use the token in the add-on:**
   - The token will only be displayed once
   - Paste it into the add-on configuration
   - Never share this token publicly

### Testing Your Firefly III Connection

You can test your Firefly III API connection:

```bash
# Replace with your Firefly III URL and token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://homeassistant.local:8080/api/v1/about
```

Expected response (success):
```json
{
  "data": {
    "version": "6.0.0",
    "api_version": "2.0.0"
  }
}
```

## Home Assistant Installation

### Step 1: Install the Add-on

1. Go to **Settings** → **Add-ons & Integrations**
2. Click the **Add-ons** tab
3. Click the three dots ⋯ menu in the top-right
4. Select **Repositories**
5. If using custom repository:
   ```
   https://github.com/yourusername/firefly-csv-importer
   ```
6. Click "Add"
7. Find "Firefly III CSV Importer" in the list
8. Click on it
9. Click **Install**

### Step 2: Configure the Add-on

1. After installation, click on "Firefly III CSV Importer"
2. Go to the **Configuration** tab
3. Enter your configuration:
   - **Firefly III Base URL:** `http://homeassistant.local:8080`
   - **Personal Access Token:** Paste your token from step 1
   - **Log Level:** `info` (or `debug` for troubleshooting)
4. Click **Save**

### Step 3: Start the Add-on

1. Go to the **Info** tab
2. Click the **Start** button
3. Check that it shows "running" status
4. Verify no errors in the logs

### Step 4: Access the Web UI

#### Via Ingress (Recommended)

1. Go back to **Home Assistant** main page
2. Look in the sidebar for **Firefly III CSV Importer**
3. Click to open the UI

#### Direct Access

- If Ingress is not available, access directly:
- `http://homeassistant.local:8099`

## Troubleshooting Installation

### Add-on Not Showing in Store

**Issue:** Can't find the add-on after adding the repository

**Solution:**
1. Go to Settings → Add-ons & Integrations → Repositories
2. Click the repository URL to verify it was added
3. Click the refresh icon (⟳) in the top-right
4. Wait 30 seconds and check again

### "Connection failed" Error

**Issue:** Add-on can't connect to Firefly III

**Solutions:**

1. **Check Firefly III URL:**
   - Verify the URL is correct
   - Make sure Firefly III is running
   - Test from Home Assistant host:
     ```bash
     curl http://homeassistant.local:8080
     ```

2. **Check Network:**
   - Ensure both services are on the same network
   - If using Docker Compose, services should be on the same network
   - For Home Assistant core installations, use the correct hostname/IP

3. **Check Token:**
   - Generate a new Personal Access Token
   - Verify no extra spaces were copied
   - Ensure the token hasn't expired

### "Invalid token" Error

**Issue:** Token is rejected by Firefly III

**Solutions:**

1. Generate a new token:
   - Log into Firefly III
   - Delete the old token
   - Create a new one
   - Copy immediately and save

2. Verify token format:
   - Token should start with no special characters
   - Should be a long alphanumeric string
   - No spaces or line breaks

### Add-on Crashes or Won't Start

**Issue:** Add-on starts but immediately stops

**Check logs:**
1. Settings → Add-ons → Firefly III CSV Importer
2. Click **Logs** tab
3. Look for error messages

**Common causes:**
- Invalid Python dependencies (check requirements.txt)
- Port 8099 already in use
- Permission issues
- Firefly III URL not configured

### High CPU or Memory Usage

**Issue:** Add-on uses excessive resources

**Solutions:**
- Limit upload file size (default: 10MB)
- Reduce number of rows per import
- Restart the add-on periodically
- Check Firefly III API performance

## Verification

### Check Add-on is Running

1. Settings → Add-ons & Integrations
2. Click "Firefly III CSV Importer"
3. Should show status "Running" with green indicator

### Test Configuration

1. Open the add-on UI
2. Go to Configuration section
3. You should see your Firefly III URL
4. Click "Save Configuration" to test the connection
5. Should show success message

### Test CSV Upload

1. Download a sample CSV from the examples directory
2. Upload it through the UI
3. Should show preview and validation results

## Next Steps

- See [README.md](README.md) for usage instructions
- See [API_EXAMPLES.md](API_EXAMPLES.md) for API documentation
- Check the examples folder for sample CSV files

## Support

For issues:
1. Check the logs in Home Assistant
2. See troubleshooting section above
3. GitHub Issues: https://github.com/yourusername/firefly-csv-importer/issues

## Advanced Configuration

### Environment Variables

You can set additional environment variables in the add-on configuration:

- `PORT` - Server port (default: 8099)
- `PYTHONUNBUFFERED` - Always set to 1 for logging
- `LOG_LEVEL` - Logging level (debug, info, warning, error)

### Firewall Rules

If using a firewall:
- Ensure port 8099 is accessible from your Home Assistant instance
- If Firefly III is on another host, ensure port 8080 (or custom port) is accessible

### Reverse Proxy

If using a reverse proxy:
- Make sure X-Forwarded-For headers are passed correctly
- Configure proper CORS if needed

## Uninstallation

1. Settings → Add-ons → Firefly III CSV Importer
2. Click the three dots ⋯ menu
3. Select "Uninstall"
4. Confirm

All data will be removed. CSV files in /tmp will be cleaned up.

---

**Installation complete! You're ready to start importing transactions! 🎉**
