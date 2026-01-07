# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install the necessary library
RUN pip install --no-cache-dir requests

# Copy your script into the container
COPY main.py .

# Command to run the script automatically when the container starts
CMD ["python", "main.py"]