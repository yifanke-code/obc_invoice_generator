FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/output && \
    chmod 755 /app/uploads /app/output && \
    touch /app/invoice_data.json && \
    chmod 666 /app/invoice_data.json

# Expose port
EXPOSE 5050

# Run the application
CMD ["python", "app.py"]
