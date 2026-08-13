FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY packages/algorithm-sdk ./packages/algorithm-sdk
COPY backend ./backend

RUN python -m pip install --no-cache-dir \
    ./packages/algorithm-sdk \
    ./backend

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000
CMD ["uvicorn", "cv_platform.main:app", "--host", "0.0.0.0", "--port", "8000"]
