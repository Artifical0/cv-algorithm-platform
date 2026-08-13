FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY database/requirements.txt ./database/requirements.txt
RUN python -m pip install --no-cache-dir -r database/requirements.txt

COPY database ./database

ENTRYPOINT ["alembic", "-c", "database/alembic.ini"]
CMD ["upgrade", "head"]
