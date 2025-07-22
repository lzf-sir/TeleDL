# Frontend Dockerfile
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the application code
COPY . .

# Expose the frontend port
EXPOSE 3000

# Run the frontend service
CMD ["npm", "run", "dev"]
