FROM python:3.12-slim

# Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p Format

EXPOSE 8000

# IMPORTANT: file app.py hai isliye "app:app" likha hai
# Render ke PORT variable ko use kar rahe hain (best practice)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
