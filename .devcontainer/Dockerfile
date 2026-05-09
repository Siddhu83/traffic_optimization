# Use a Python image that already has common tools installed
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies for OpenCV (The Vision "Eyes")
# These are required to process images and video feeds
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt-get/lists/*

# Pre-install the core libraries so the team doesn't wait
# ultralytics = YOLO Vision
# crewai = Agent Orchestration
# fastapi = For the Dashboard backend
RUN pip install --no-cache-dir \
    ultralytics \
    crewai \
    langchain-google-genai \
    fastapi \
    uvicorn \
    python-dotenv