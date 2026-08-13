FROM pytorch/pytorch:2.10.0-cuda12.6-cudnn9-runtime

WORKDIR /app

COPY packages/algorithm-sdk /workspace/packages/algorithm-sdk
COPY examples/faster-rcnn /workspace/examples/faster-rcnn

RUN pip install --no-cache-dir \
    /workspace/packages/algorithm-sdk \
    /workspace/examples/faster-rcnn

COPY examples/faster-rcnn/manifest.yaml /app/manifest.yaml
COPY examples/faster-rcnn/model-config.yaml /app/model-config.example.yaml
COPY examples/faster-rcnn/service.py /app/service.py

ENV CV_FASTER_RCNN_MODE=torchvision \
    CV_FASTER_RCNN_CONFIG=/models/model-config.yaml \
    CV_FASTER_RCNN_WEIGHTS=/models/model.pth \
    CV_FASTER_RCNN_DATA_ROOT=/data \
    CV_FASTER_RCNN_DEVICE=auto

EXPOSE 8000

RUN useradd --create-home --uid 10001 algorithm && chown -R algorithm:algorithm /app
USER 10001

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
