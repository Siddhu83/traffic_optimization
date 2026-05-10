# Use a more stable base
FROM mcr.microsoft.com/devcontainers/python:3.11

# Fix: Set frontend to noninteractive and combine commands
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -yq && apt-get install -yq --no-install-recommends \
    libgl1-mesa-dev \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# The rest of your pip installs...
RUN pip install --no-cache-dir \
    ultralytics \
    crewai \
    langchain-google-genai \
    langchain-groq \
    fastapi \
    uvicorn \
    streamlit \
    pandas \
    plotly \
    streamlit-echarts \
    pydantic \
    PyYAML \
    python-dotenv
