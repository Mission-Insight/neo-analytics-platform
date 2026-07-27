FROM python:3.10.11-slim

WORKDIR /app

# Installing dependencies before copying the rest of the source lets Docker
# cache this layer — a rebuild after a code-only change skips reinstalling.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# --server.address=0.0.0.0 is required: Streamlit's default binds to
# localhost only, which is unreachable from outside the container even with
# the port published. --server.headless=true skips the browser-launch
# attempt, which would otherwise fail in a container with no display.
CMD ["streamlit", "run", "src/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
