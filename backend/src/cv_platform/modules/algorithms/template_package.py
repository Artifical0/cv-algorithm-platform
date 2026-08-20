from base64 import b64decode
from io import BytesIO
from textwrap import dedent
from zipfile import ZIP_DEFLATED, ZipFile

from cv_algorithm_sdk import ResultType

TASK_LABELS = {
    ResultType.OBJECT_DETECTION: ("目标检测", "Object Detection"),
    ResultType.CLASSIFICATION: ("图像分类", "Classification"),
    ResultType.SEGMENTATION: ("图像分割", "Segmentation"),
    ResultType.OCR: ("文字识别", "OCR"),
    ResultType.POSE_ESTIMATION: ("姿态估计", "Pose Estimation"),
}

SAMPLE_JPEG = b64decode(
    "/9j/4AAQSkZJRgABAQEAagBqAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH"
    "BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME"
    "BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU"
    "FBQUFBQUFBQUFBQUFBT/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEA"
    "AAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIh"
    "MUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6"
    "Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZ"
    "mqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx"
    "8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREA"
    "AgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAV"
    "YnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hp"
    "anN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPE"
    "xcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9"
    "U6KKKAP/2Q=="
)


def build_algorithm_template(task_type: ResultType) -> BytesIO:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("manifest.yaml", _manifest(task_type))
        archive.writestr("service.py", SERVICE_SOURCE)
        archive.writestr("algorithm.py", ALGORITHM_SOURCE)
        archive.writestr("requirements.txt", REQUIREMENTS_SOURCE)
        archive.writestr("README.md", _readme(task_type))
        archive.writestr("test/sample.jpg", SAMPLE_JPEG)
        archive.writestr("weights/README.txt", "将模型权重放在此目录；无权重时可删除本目录。\n")
    buffer.seek(0)
    return buffer


def template_filename(task_type: ResultType) -> str:
    return f"cv-algorithm-{task_type.value}-template.zip"


def _manifest(task_type: ResultType) -> str:
    chinese_name, english_name = TASK_LABELS[task_type]
    return dedent(
        f"""\
        schema_version: "1.0"
        id: template-{task_type.value.replace('_', '-')}
        name: {english_name} Template
        version: 0.1.0
        description: 可运行的{chinese_name}接入模板，请替换示例推理逻辑
        task_type: {task_type.value}
        runtime:
          framework: onnx
          device: cpu
          min_memory_mb: 512
        input:
          media_types: [image/jpeg, image/png, image/webp]
        output:
          type: {task_type.value}
        parameters:
          confidence:
            type: number
            default: 0.5
            minimum: 0
            maximum: 1
            step: 0.05
            title: 置信度阈值
            description: 过滤低置信度结果
          max_results:
            type: integer
            default: 100
            minimum: 1
            maximum: 1000
            step: 1
            title: 最大结果数量
          use_half:
            type: boolean
            default: false
            title: FP16 推理
          mode:
            type: string
            default: balanced
            options: [fast, balanced, accurate]
            title: 推理模式
        """
    )


SERVICE_SOURCE = dedent(
    """\
    from pathlib import Path

    from cv_algorithm_sdk import load_manifest
    from cv_algorithm_sdk.server import create_algorithm_app

    from algorithm import TemplateAlgorithm


    BASE_DIR = Path(__file__).resolve().parent
    manifest = load_manifest(BASE_DIR / "manifest.yaml")
    app = create_algorithm_app(TemplateAlgorithm(manifest))
    """
)


ALGORITHM_SOURCE = dedent(
    """\
    from cv_algorithm_sdk import (
        AlgorithmIdentity,
        AlgorithmResult,
        ClassificationData,
        ClassificationResult,
        DetectionAlgorithm,
        ImageMetadata,
        ObjectDetectionData,
        ObjectDetectionResult,
        OcrData,
        OcrResult,
        PoseData,
        PoseEstimationResult,
        PredictRequest,
        SegmentationData,
        SegmentationResult,
        TimingMetadata,
    )


    class TemplateAlgorithm(DetectionAlgorithm):
        def load(self) -> None:
            # 在这里加载 weights/ 中的模型文件，只执行一次。
            self.model = None

        def predict(self, request: PredictRequest) -> AlgorithmResult:
            # TODO: 读取 request.input.asset_uri，使用 request.parameters 执行真实推理。
            common = {
                "request_id": request.request_id,
                "algorithm": AlgorithmIdentity(id=self.manifest.id, version=self.manifest.version),
                "input": ImageMetadata(width=1, height=1),
                "timing": TimingMetadata(),
            }
            output_type = self.manifest.output.type.value
            if output_type == "object_detection":
                return ObjectDetectionResult(**common, data=ObjectDetectionData(detections=[]))
            if output_type == "classification":
                return ClassificationResult(**common, data=ClassificationData(predictions=[]))
            if output_type == "segmentation":
                return SegmentationResult(**common, data=SegmentationData(segments=[]))
            if output_type == "ocr":
                return OcrResult(**common, data=OcrData(texts=[]))
            return PoseEstimationResult(**common, data=PoseData(instances=[]))
    """
)


REQUIREMENTS_SOURCE = dedent(
    """\
    # 平台已提供 fastapi、uvicorn、pydantic、PyYAML 和 cv_algorithm_sdk。
    # 在下方添加模型推理所需的额外依赖，并固定版本，例如：
    # onnxruntime==1.22.1
    """
)


def _readme(task_type: ResultType) -> str:
    chinese_name, _ = TASK_LABELS[task_type]
    return dedent(
        f"""\
        # {chinese_name}算法接入模板

        这是一个可以通过平台 manifest 校验和三接口协议验收的最小模板。默认返回空结果，
        请在 `algorithm.py` 中替换为真实模型加载和推理逻辑。

        ## 接入步骤

        1. 修改 `manifest.yaml` 中的 `id`、`name`、`version`、运行环境和参数。
        2. 将模型文件放入 `weights/`，在 `TemplateAlgorithm.load()` 中加载。
        3. 在 `predict()` 中读取 `request.input.asset_uri` 和 `request.parameters`。
        4. 返回与 `{task_type.value}` 对应的 SDK Result 类型。
        5. 用真实图片替换 `test/sample.jpg`，该图片会用于构建后的 `/predict` 验收。
        6. 将本目录内容直接压缩为 ZIP；`manifest.yaml` 必须位于 ZIP 根目录。
        7. 在算法中心导入 ZIP，校验通过后点击“构建并发布”。

        ## 必需接口

        `service.py` 已通过平台 SDK 提供：

        - `GET /health`
        - `GET /metadata`
        - `POST /predict`

        ## 安全限制

        不要加入自定义 Dockerfile、绝对路径、符号链接或设备文件。依赖写入
        `requirements.txt`，平台会使用受控运行时模板构建镜像。
        """
    )
