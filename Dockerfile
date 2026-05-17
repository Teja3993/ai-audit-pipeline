# Use the official lightweight Python image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files 
# and to ensure stdout is logged immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# ---------------------------------------------------------
# Install OS-level dependencies for WeasyPrint
# ---------------------------------------------------------
# WeasyPrint requires specific C-libraries to render HTML/CSS to PDF
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Install Python Dependencies
# ---------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Copy Application Code
# ---------------------------------------------------------
# Copy the rest of the application code into the container
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]