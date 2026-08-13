FROM ultralytics/ultralytics:8.3.0

WORKDIR /app

COPY packages/algorithm-sdk /workspace/packages/algorithm-sdk
COPY examples/yolo /workspace/examples/yolo

RUN pip install --no-cache-dir \
    /workspace/packages/algorithm-sdk \
    /workspace/examples/yolo

COPY examples/yolo/manifest.yaml /app/manifest.yaml
COPY examples/yolo/service.py /app/service.py

ENV CV_YOLO_MODE=ultralytics \
    CV_YOLO_WEIGHTS=/models/model.pt \
    CV_YOLO_DATA_ROOT=/data \
    CV_YOLO_DEVICE=auto

EXPOSE 8000
RUN useradd --create-home --uid 10001 algorithm && chown -R algorithm:algorithm /app
USER 10001
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
