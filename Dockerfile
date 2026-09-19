# =========================================================================
# Dockerfile: Smart Energy Monitoring & Industrial EMS System
# Multi-runtime image supporting Python FastAPI Backend + Java Microservice
# =========================================================================

FROM python:3.11-slim

# Install system utilities, OpenJDK Java runtime, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements & install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application source
COPY . .

# Compile Java Microservice
RUN mkdir -p java_service/bin && \
    javac -d java_service/bin java_service/src/main/java/com/energy/EnergyComplianceApplication.java

# Make launch scripts executable
RUN chmod +x run.py run.sh

# Expose ports: 8000 (FastAPI Web + WebSocket), 8081 (Java ISO 50001 Engine)
EXPOSE 8000 8081

# Default startup command
CMD ["python3", "run.py"]
