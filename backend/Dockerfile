FROM python:3.12-slim

# Set working directory
WORKDIR /app/src

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . ./backend

# Expose the port and run the Flask app
ENV PYTHONPATH=/app/src

CMD ["flask", "--app", "backend.app.app", "run", "--host=0.0.0.0", "--port=5000"]