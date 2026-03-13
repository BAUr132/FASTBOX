# Use Node.js LTS
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies and start dev server with host 0.0.0.0 for Docker access
# Note: npm install will run every time if we don't use volumes properly
# but for MVP this is the most reliable way.
CMD sh -c "npm install && npm run dev -- --host 0.0.0.0"

EXPOSE 5173
