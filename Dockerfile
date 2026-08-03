FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ ./server/

# Expose the C2 port
EXPOSE 5555

# Run the server
CMD ["python", "-m", "server.server"]
