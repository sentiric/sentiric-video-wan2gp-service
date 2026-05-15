import os

class Settings:
    APP_NAME = "Sentiric Wan2GP Video Engine"
    APP_VERSION = "1.0.0"
    ENV = os.getenv("ENV", "production")
    DEVICE = "cuda"
    # Wan2.1 1.3B (Düşük kaynaklı video üretimi için ideal)
    MODEL_ID = os.getenv("WAN2GP_MODEL_ID", "Wan-AI/Wan2.1-T2V-1.3B")
    
    HTTP_PORT = int(os.getenv("WAN2GP_SERVICE_HTTP_PORT", "16120"))
    GRPC_PORT = int(os.getenv("WAN2GP_SERVICE_GRPC_PORT", "16121"))
    METRICS_PORT = int(os.getenv("WAN2GP_SERVICE_METRICS_PORT", "16122"))

    # mTLS
    GRPC_TLS_CA_PATH = os.getenv("GRPC_TLS_CA_PATH", "/sentiric-certificates/certs/ca.crt")
    CERT_PATH = "/sentiric-certificates/certs/video-wan2gp-service-chain.crt"
    KEY_PATH = "/sentiric-certificates/certs/video-wan2gp-service.key"

    # Storage & MQ
    S3_ENDPOINT = os.getenv("BUCKET_ENDPOINT_URL", "http://minio:9000")
    S3_ACCESS_KEY = os.getenv("BUCKET_ACCESS_KEY_ID", "sentiric")
    S3_SECRET_KEY = os.getenv("BUCKET_SECRET_ACCESS_KEY", "sentiric-secret-key")
    S3_BUCKET = os.getenv("BUCKET_NAME", "sentiric")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://sentiric:sentiric_pass@rabbitmq:5672/%2f")

settings = Settings()