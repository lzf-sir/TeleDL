# Backend Dockerfile
FROM python:3.9-slim-bullseye

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install SQLite and libmagic
RUN apt-get update && apt-get install -y sqlite3 libmagic1 && rm -rf /var/lib/apt/lists/*

# Set environment variable for SQLite database
ENV DATABASE_URL sqlite:///app/db.sqlite3

# Copy the application code
COPY . .

# Expose the backend port
EXPOSE 8848

# Run the backend service
CMD ["python", "main.py"]
