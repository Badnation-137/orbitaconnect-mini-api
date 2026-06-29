#!/bin/bash
# OrbitaConnect Auto-Deployment Script

# 1. Update System & Install Dependencies
dnf update -y
dnf install -y python3.11 pip git aws-cli

# 2. Setup Folder Aplikasi di Home Directory (Avoid Permission Issues)
mkdir -p /home/ec2-user/orbitaconnect
chown ec2-user:ec2-user /home/ec2-user/orbitaconnect

# 3. Clone Source Code dari GitHub sebagai ec2-user
sudo -u ec2-user git clone https://github.com/Badnation-137/orbitaconnect-mini-api /home/ec2-user/orbitaconnect

# 4. Fix Frontend API URL (Ganti localhost jadi relative path)
cd /home/ec2-user/orbitaconnect/frontend
sudo -u ec2-user sed -i "s|'http://localhost:8000'|''|g" index.html

# 5. Install Python Libraries sebagai ec2-user
sudo -u ec2-user pip3 install fastapi uvicorn psycopg2-binary pydantic

# 6. Buat Service File agar App Jalan Otomatis & Restart jika Crash
cat <<EOF > /etc/systemd/system/orbita.service
[Unit]
Description=OrbitaConnect FastAPI Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/orbitaconnect
Environment="DATABASE_URL=postgresql://ota_db_user:\$ecurepass2026!@orbita-db.cuo4i5zanmop.us-east-1.rds.amazonaws.com:5432/orbitaconnect"
ExecStart=/usr/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. Enable & Start Service
systemctl daemon-reload
systemctl enable orbita
systemctl start orbita

echo "Deployment Selesai! Cek status dengan: systemctl status orbita"