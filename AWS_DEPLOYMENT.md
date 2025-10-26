# AWS Deployment Guide - Detailed Steps

##  Architecture

```
User Browser
    ↓
Nginx (Port 80)
    ↓
Docker Container (Flask on Port 5000)
    ↓
EC2 Instance (Free Tier t2.micro)
```

---

##  STEP 1: GitHub Setup (LOCAL COMPUTER)

### 1.1 Create GitHub Account
- Go to https://github.com
- Sign up with email

### 1.2 Create Repository
1. Click "+" → "New repository"
2. Name: `license-plate-detection`
3. Description: "License plate detection using YOLO and PaddleOCR"
4. Public (so you can clone without credentials)
5. Click "Create repository"

### 1.3 Push Your Code

**On Windows Command Prompt (in your project folder):**

```bash
# Navigate to project
cd D:\ml\number_plate_detection

# Initialize git
git init

# Add all files
git add .

# Create commit
git commit -m "Initial commit: License plate detection app"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/license-plate-detection.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

**Verify on GitHub.com** - You should see your code!

---

##  STEP 2: AWS Account Setup

### 2.1 Create Free AWS Account
1. Go to https://aws.amazon.com/free
2. Click "Create a free account"
3. Enter email address
4. Set password
5. Add payment method (won't be charged for free tier)
6. Verify phone number
7. Complete signup

### 2.2 Create IAM User (Recommended)
1. Go to AWS Console
2. Search "IAM"
3. Click "Users" → "Create user"
4. Name: `license-plate-dev`
5. Click "Next"
6. Attach policy: `AdministratorAccess` (for testing)
7. Create user
8. Download credentials CSV (save safely)

---

##  STEP 3: Launch EC2 Instance

### 3.1 Open EC2 Console
1. Log in to AWS Console
2. Search "EC2"
3. Click "EC2 Dashboard"
4. Click "Instances" (left sidebar)
5. Click "Launch instances"

### 3.2 Configure Instance

**Step 1: Name and OS**
- Name: `license-plate-app`
- AMI: Ubuntu 22.04 LTS (free tier eligible)
- Architecture: 64-bit (x86)

**Step 2: Instance Type**
- Type: `t2.micro` (FREE TIER)
- Free tier eligible checkbox should be checked

**Step 3: Key Pair**
- Click "Create new key pair"
- Name: `license-plate-key`
- Type: RSA
- Format: .pem
- Click "Create key pair"
- **Downloads automatically - SAVE THIS FILE!**

**Step 4: Network Settings**
- VPC: default
- Subnet: any default
- Public IP: Enable
- Security group: "Create new"
  - Name: `plate-detection-sg`
  - Description: "For license plate detection app"
  
**Security Group Rules:**
Click "Add security group rule" for each:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| SSH | TCP | 22 | My IP |
| HTTP | TCP | 80 | Anywhere (0.0.0.0/0) |
| HTTPS | TCP | 443 | Anywhere (0.0.0.0/0) |
| Custom TCP | TCP | 5000 | Anywhere (0.0.0.0/0) |

**Step 5: Storage**
- Size: 30 GB (free tier limit)
- Volume type: gp2
- Delete on termination: Yes

**Step 6: Summary**
- Review all settings
- Click "Launch instance"

### 3.3 Wait for Instance to Start
- Go to "Instances"
- Wait for "Instance State" = "running"
- Status checks = "2/2 checks passed"

### 3.4 Get Public IP
1. Click on your instance
2. Copy "Public IPv4 address" (e.g., `54.123.456.789`)

---

##  STEP 4: Connect to EC2 via SSH

### For Windows (Using WSL or PowerShell)

**Option A: Using Windows Terminal/PowerShell**

```bash
# Navigate to folder with your .pem file
cd D:\path\to\license-plate-key.pem

# Change permissions (one time)
# (Skip if on Windows)

# Connect to EC2
ssh -i license-plate-key.pem ubuntu@your-public-ip
```

Replace `your-public-ip` with your actual IP (e.g., `54.123.456.789`)

**Option B: Using PuTTY**
1. Download PuTTY: https://www.putty.org/
2. Use PuTTYgen to convert .pem to .ppk
3. Open PuTTY
4. Host: `ubuntu@your-public-ip`
5. Auth: Select .ppk file
6. Open

---

##  STEP 5: Install Docker on EC2

### After SSH Connected:

```bash
# Update package manager
sudo apt update
sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose git

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Verify installation
docker --version
docker-compose --version
git --version
```

**Log out and back in for group changes:**
```bash
exit
# SSH back in
ssh -i license-plate-key.pem ubuntu@your-public-ip
```

---

##  STEP 6: Clone and Run Your App

### On EC2:

```bash
# Clone your repository (replace YOUR_USERNAME)
git clone https://github.com/YOUR_USERNAME/license-plate-detection.git

# Navigate to project
cd license-plate-detection

# Verify files exist
ls -la

# Build Docker image (takes 5-10 minutes first time)
docker build -t license-plate-detection .

# Run container
docker-compose up -d

# Check if running
docker ps

# View logs
docker logs -f license-plate-detection
```

**First build will take time** - It's downloading models (500MB+)

---

##  STEP 7: Test Access

### Access Your App

Open browser and go to:
```
http://your-public-ip:5000
```

Replace `your-public-ip` with your EC2 public IP

 You should see the upload page!

---

##  STEP 8: Setup Nginx Reverse Proxy (Optional)

### Access on Port 80 Instead of 5000

```bash
# Install Nginx
sudo apt install -y nginx

# Edit Nginx config
sudo nano /etc/nginx/sites-available/default
```

**Delete all content and paste:**
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 500M;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

**Save (Ctrl+O → Enter → Ctrl+X)**

```bash
# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable on boot
sudo systemctl enable nginx
```

**Now access at:**
```
http://your-public-ip
```
(Without :5000)

---

##  STEP 9: Manage Your App

### View Logs
```bash
docker logs -f license-plate-detection
```

### Stop Container
```bash
docker-compose down
```

### Restart Container
```bash
docker-compose up -d
```

### Restart EC2 Instance
```bash
# From AWS Console
# Instances → Right-click → Instance State → Reboot
```

---

##  STEP 10: Update App with New Code

### When You Push Updates to GitHub

```bash
# SSH into EC2
ssh -i license-plate-key.pem ubuntu@your-public-ip

# Navigate to project
cd license-plate-detection

# Pull latest code
git pull origin main

# Rebuild image
docker build -t license-plate-detection .

# Restart container
docker-compose down
docker-compose up -d

# Check logs
docker logs -f license-plate-detection
```

---

##  Monitor Free Tier Usage

### Check Costs
1. AWS Console → Billing
2. Check EC2 usage
3. Check data transfer

### Free Tier Limits
-  **EC2:** 750 hours/month
-  **Storage:** 30 GB EBS
-  **Data Transfer:** 100 GB/month outbound
-  **Expires:** After 12 months

---

##  Troubleshooting

### Can't Connect to EC2
```bash
# Check security group allows SSH on port 22
# Check .pem file permissions
# Try from AWS Console EC2 Instance Connect
```

### Docker Build Fails
```bash
# Rebuild without cache
docker build --no-cache -t license-plate-detection .

# Check logs
docker logs license-plate-detection

# Check disk space
df -h
```

### App Not Accessible
```bash
# Check if container is running
docker ps

# Check firewall rules
sudo ufw status

# Check Nginx
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Out of Storage
```bash
# Check disk usage
df -h

# Clean Docker images
docker system prune -a

# Remove old logs
sudo find /var/log -type f -name "*.log" -delete
```

---

##  Final Checklist

-  GitHub account created
-  Code pushed to GitHub
-  AWS account created
-  EC2 instance running
-  Docker installed
-  App running
-  Can access app in browser
-  Security group configured
-  Ready for production!

---

##  Getting Help

1. **Docker Issues:** `docker logs license-plate-detection`
2. **Connection Issues:** Check security group rules
3. **Performance Issues:** Check EC2 CloudWatch metrics
4. **Storage Issues:** Delete old files in static/uploads/

---

##  You're Live!

Your app is now running on AWS Free Tier!

### Share Your App
```
http://your-public-ip
```

### Keep It Running (12 months free)
- Monitor billing
- Check instance monthly
- Keep backups of code on GitHub

**Congratulations!** 