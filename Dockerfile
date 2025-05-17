# Dockerfile for Mi360 2K P2P→RTSP Python server

FROM ubuntu:20.04

# Install OS packages (including GStreamer RTSP bindings for Python)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      python3 python3-pip python3-gi gir1.2-gst-rtsp-server-1.0 \
      python3-dev libgirepository1.0-dev pkg-config \
      gstreamer1.0-tools gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good gstreamer1.0-libav && \
    rm -rf /var/lib/apt/lists/*

# Install the one Python package we need from PyPI
RUN pip3 install pycryptodome

WORKDIR /app

# Copy our RTSP server script into the image
COPY Mi360RtspServer.py ./

# Environment variables (can be overridden in Portainer or docker-compose)
ENV CAMERA_IP=192.168.1.42
ENV RTSP_PORT=8554

# Expose the RTSP port
EXPOSE ${RTSP_PORT}

# Run the script directly (it reads CAMERA_IP and RTSP_PORT)
CMD ["python3", "Mi360RtspServer.py"]
