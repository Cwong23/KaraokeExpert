FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port and run the Flask app
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

CMD ["sh", "-c", "flask run --host=0.0.0.0 --port=${PORT:-5000}"]