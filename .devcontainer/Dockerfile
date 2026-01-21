FROM mcr.microsoft.com/devcontainers/python:3.11

# Install FFmpeg with AV1 + FLAC support
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libaom-dev \
    libdav1d-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ensure ffmpeg is visible
RUN ffmpeg -version

WORKDIR /workspace
