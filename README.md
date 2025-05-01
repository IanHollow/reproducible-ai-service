# Reproducible AI Inference Microservice

## Getting Started Locally

Follow these steps to run the service on your local machine:

1. **Clone the repository**

   ```bash
   git clone https://github.com/IanHollow/reproducible-ai-service.git
   cd reproducible-ai-service
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # .venv\Scripts\activate  # Windows PowerShell
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run the API server**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Test the `/predict` endpoint**
   ```bash
   curl -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d '{"text":"I absolutely love this service!"}'
   ```

You should receive a JSON response with a sentiment label and confidence score:

```json
{
  "label": "POSITIVE",
  "score": 0.9987
}
```

## Running with Docker

You can also run the service using Docker for better isolation and reproducibility.

1.  **Build the Docker image:**
    ```bash
    docker build -t reproducible-ai-service .
    ```

2.  **(Optional) Create a `.env` file:**
    Copy the example file and customize if needed:
    ```bash
    cp .env.example .env
    # Modify .env with your desired settings (e.g., change API_PORT)
    ```

3.  **Run the Docker container:**
    *   **Without `.env` file (using defaults or system env vars):**
        ```bash
        docker run -p 8000:8000 --rm reproducible-ai-service
        ```
        *(Note: If you changed `API_PORT` via system environment variables, adjust the `-p` mapping accordingly, e.g., `-p <host_port>:<container_port>`)*

    *   **With `.env` file:**
        Pass the environment variables from your `.env` file to the container:
        ```bash
        docker run -p 8000:8000 --env-file .env --rm reproducible-ai-service
        ```
        *(Adjust the `-p <host_port>:<container_port>` mapping if you changed `API_PORT` in your `.env` file)*

4.  **Test the endpoint (from your host machine):**
    ```bash
    curl -X POST http://localhost:8000/predict \
      -H 'Content-Type: application/json' \
      -d '{"text":"Docker makes deployment easy!"}'
    ```

## Configuration

The application can be configured using environment variables. Create a `.env` file in the project root (copy from `.env.example`) or set system environment variables.

-   `API_PORT`: The port the FastAPI server will listen on (default: `8000`).
-   `MODEL_NAME`: The HuggingFace model identifier to load (default: `distilbert-base-uncased-finetuned-sst-2-english`).
-   `LOG_LEVEL`: The logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) (default: `INFO`).
