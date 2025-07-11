# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY . /app

# Install Flask
RUN pip install flask

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]