ARG FASTER_RCNN_BASE_IMAGE=pytorch/pytorch:2.10.0-cuda12.6-cudnn9-runtime
FROM ${FASTER_RCNN_BASE_IMAGE}

WORKDIR /app

COPY packages/algorithm-sdk /workspace/packages/algorithm-sdk
COPY examples/faster-rcnn /workspace/examples/faster-rcnn

ARG PIP_INDEX_URL=https://pypi.org/simple
RUN python3 -m pip install --no-cache-dir --prefer-binary \
    --timeout 120 --retries 20 --index-url "${PIP_INDEX_URL}" \
    "fastapi>=0.104,<1" \
    "pydantic>=2.10,<3" \
    "uvicorn>=0.24,<1"

COPY examples/faster-rcnn/manifest.yaml /app/manifest.yaml
COPY examples/faster-rcnn/model-config.yaml /app/model-config.example.yaml
COPY examples/faster-rcnn/service.py /app/service.py

ENV PYTHONPATH=/workspace/packages/algorithm-sdk/src:/workspace/examples/faster-rcnn/src \
    CV_FASTER_RCNN_MODE=torchvision \
    CV_FASTER_RCNN_CONFIG=/models/model-config.yaml \
    CV_FASTER_RCNN_WEIGHTS=/models/model.pth \
    CV_FASTER_RCNN_DATA_ROOT=/data \
    CV_FASTER_RCNN_DEVICE=auto

EXPOSE 8000

RUN useradd --create-home --uid 10001 algorithm && chown -R algorithm:algorithm /app
USER 10001

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python3", "-m", "uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
