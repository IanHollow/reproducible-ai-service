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
