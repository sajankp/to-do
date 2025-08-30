FROM python:3.10.15-slim AS builder

RUN useradd -m appuser
USER appuser
WORKDIR /code

# Install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.10.15-slim

# Create app user early
RUN useradd -m appuser
USER appuser

WORKDIR /code

# Copy only app code
COPY --from=builder /home/appuser/.local /home/appuser/.local
COPY ./app ./app

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
