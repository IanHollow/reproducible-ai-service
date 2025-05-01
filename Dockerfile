# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and group
RUN groupadd --gid 1001 pythonuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home pythonuser

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for certain ML libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container and change ownership
COPY --chown=pythonuser:pythonuser requirements.txt .

# Install any needed packages specified in requirements.txt as the non-root user
# Use --no-cache-dir to reduce image size
# Use --user flag to install packages in the user's home directory site-packages
USER pythonuser

# Add the user's local bin directory to the PATH *before* installing packages
# This ensures that installed executables like uvicorn are found immediately
ENV PATH="/home/pythonuser/.local/bin:${PATH}"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Copy the application code into the container and change ownership
# Switch back to root temporarily for COPY --chown
USER root
COPY --chown=pythonuser:pythonuser ./app /app/app

# Switch back to the non-root user
USER pythonuser

# Make port 8000 available to the world outside this container (default, can be overridden)
EXPOSE 8000

# Define environment variable for the port (can be overridden at runtime)
ENV API_PORT=8000

# Run uvicorn when the container launches as the non-root user
# Use sh -c within exec form for robust variable substitution
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}"]
