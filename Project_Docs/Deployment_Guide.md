# Deployment Guide - ThinkBot

## Overview
This guide provides comprehensive instructions for deploying ThinkBot in various environments, from local development to production deployment.

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM (1GB recommended)
- **Storage**: 100MB for application + data storage
- **Network**: Internet connection for AI service

### Required Services
- **Google Gemini AI**: API key required
- **Web Server**: For production deployment
- **Database**: Optional (currently uses JSON files)

---

## Local Development

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/thinkbot.git
cd thinkbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Set environment variables
export GEMINI_API_KEY="your-gemini-api-key-here"
export DEBUG=True
export HOST="0.0.0.0"
export PORT=8001
```

### 3. Start Development Server
```bash
# Start with auto-reload
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8001

# Or start directly
python api.py
```

### 4. Access Application
- **URL**: `http://localhost:8001`
- **API Docs**: `http://localhost:8001/docs`
- **Alternative API Docs**: `http://localhost:8001/redoc`

---

## Production Deployment

### Option 1: Vercel (Recommended)

#### 1. Prepare for Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login
```

#### 2. Create vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api.py"
    }
  ],
  "env": {
    "GEMINI_API_KEY": "@gemini-api-key"
  }
}
```

#### 3. Deploy
```bash
# Deploy to Vercel
vercel

# Set environment variables
vercel env add GEMINI_API_KEY
```

### Option 2: Heroku

#### 1. Create Procfile
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

#### 2. Create runtime.txt
```
python-3.8.10
```

#### 3. Deploy
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set GEMINI_API_KEY="your-api-key"

# Deploy
git push heroku main
```

### Option 3: Railway

#### 1. Connect Repository
- Go to [Railway](https://railway.app)
- Connect your GitHub repository
- Select the thinkbot repository

#### 2. Configure Environment
- Set `GEMINI_API_KEY` environment variable
- Railway will automatically detect Python and install dependencies

#### 3. Deploy
- Railway will automatically deploy on every push to main branch
- Access your app at the provided Railway URL

### Option 4: AWS/GCP/Azure

#### 1. Create Virtual Machine
- **AWS**: EC2 instance (t2.micro minimum)
- **GCP**: Compute Engine instance
- **Azure**: Virtual Machine

#### 2. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip python3-venv -y

# Install Nginx (optional)
sudo apt install nginx -y
```

#### 3. Deploy Application
```bash
# Clone repository
git clone https://github.com/yourusername/thinkbot.git
cd thinkbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-api-key"
export DEBUG=False
export HOST="0.0.0.0"
export PORT=8001

# Start application
python -m uvicorn api:app --host 0.0.0.0 --port 8001
```

#### 4. Configure Nginx (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8001

# Start application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. Create docker-compose.yml
```yaml
version: '3.8'

services:
  thinkbot:
    build: .
    ports:
      - "8001:8001"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DEBUG=False
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### 3. Deploy with Docker
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Environment Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini AI API key | None | Yes |
| `DEBUG` | Enable debug mode | `False` | No |
| `HOST` | Host to bind to | `0.0.0.0` | No |
| `PORT` | Port to bind to | `8001` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Configuration Files

#### .env File
```bash
# Create .env file
GEMINI_API_KEY=your-gemini-api-key-here
DEBUG=False
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=INFO
```

#### config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8001))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

---

## Security Considerations

### 1. API Key Security
- **Never commit API keys to version control**
- **Use environment variables for sensitive data**
- **Rotate API keys regularly**
- **Use different keys for different environments**

### 2. Network Security
- **Use HTTPS in production**
- **Configure firewall rules**
- **Implement rate limiting**
- **Use reverse proxy (Nginx) for additional security**

### 3. Data Security
- **Encrypt sensitive data at rest**
- **Use secure data transmission**
- **Implement proper access controls**
- **Regular security audits**

### 4. Application Security
- **Validate all inputs**
- **Implement proper error handling**
- **Use secure coding practices**
- **Regular dependency updates**

---

## Monitoring and Logging

### 1. Application Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('thinkbot.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Health Checks
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### 3. Monitoring Tools
- **Prometheus + Grafana**: For metrics and visualization
- **ELK Stack**: For log aggregation and analysis
- **Sentry**: For error tracking and monitoring
- **Uptime Robot**: For uptime monitoring

---

## Performance Optimization

### 1. Application Performance
- **Use connection pooling**
- **Implement caching**
- **Optimize database queries**
- **Use async/await where appropriate**

### 2. Server Performance
- **Use multiple workers**
- **Implement load balancing**
- **Use CDN for static assets**
- **Optimize server configuration**

### 3. Database Performance
- **Use proper indexing**
- **Implement query optimization**
- **Use connection pooling**
- **Monitor query performance**

---

## Backup and Recovery

### 1. Data Backup
```bash
# Backup student data
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backups/thinkbot-$DATE.tar.gz /path/to/thinkbot/data/
```

### 2. Recovery Procedures
```bash
# Restore from backup
tar -xzf backup-20240101.tar.gz

# Verify data integrity
python -c "import json; json.load(open('data/student_test.json'))"
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>

# Or use different port
export PORT=8002
```

#### 2. API Key Issues
```bash
# Check API key
echo $GEMINI_API_KEY

# Test API key
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models"
```

#### 3. Permission Issues
```bash
# Fix file permissions
chmod -R 755 /path/to/thinkbot
chown -R www-data:www-data /path/to/thinkbot
```

#### 4. Memory Issues
```bash
# Check memory usage
free -h

# Increase swap space
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Debug Mode
```bash
# Enable debug mode
export DEBUG=True

# Start with debug logging
python -m uvicorn api:app --reload --log-level debug
```

---

## Scaling Considerations

### 1. Horizontal Scaling
- **Load balancer**: Distribute traffic across multiple instances
- **Multiple workers**: Run multiple application instances
- **Database clustering**: Use database clusters for high availability

### 2. Vertical Scaling
- **Increase server resources**: More CPU, RAM, storage
- **Optimize application**: Better algorithms and data structures
- **Use faster hardware**: SSD storage, faster network

### 3. Caching
- **Redis**: For session storage and caching
- **CDN**: For static assets
- **Application caching**: Cache frequently accessed data

---

## Maintenance

### 1. Regular Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update system packages
sudo apt update && sudo apt upgrade -y
```

### 2. Monitoring
- **Check application logs regularly**
- **Monitor system resources**
- **Set up alerts for critical issues**
- **Regular health checks**

### 3. Backup Verification
- **Test backup restoration regularly**
- **Verify data integrity**
- **Document recovery procedures**
- **Train team on recovery processes**

---

## Support

### Getting Help
- **Documentation**: Check comprehensive documentation in `Project_Docs/`
- **GitHub Issues**: Report bugs and request features
- **Community**: Join discussions and get community support
- **Professional Support**: Contact developer for enterprise support

### Contact Information
- **Developer**: Aditya Kasyap
- **Email**: [Contact through GitHub]
- **Website**: [adityakasyap.com](https://www.adityakasyap.com)
- **GitHub**: [github.com/yourusername](https://github.com/yourusername)

---

*This deployment guide is part of the ThinkBot project documentation suite.*
