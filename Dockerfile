# Dockerfile for Mi360 P2P -> RTSP server with env-config
FROM ubuntu:20.04

# Install OS dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip python3-gi gir1.2-gst-rtsp-server-1.0 \
    gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-libav && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install pycryptodome pygobject

WORKDIR /app

# Copy application code
COPY Mi360RtspServer.py ./

# Default environment variables (can be overridden in Portainer or compose)
ENV CAMERA_IP=192.168.1.42
ENV RTSP_PORT=8554

EXPOSE $RTSP_PORT

# Launch the RTSP server
CMD ["python3", "Mi360RtspServer.py"]
