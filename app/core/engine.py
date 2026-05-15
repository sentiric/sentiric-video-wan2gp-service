import torch, uuid, os, boto3, asyncio, structlog, aio_pika
from diffusers import WanVideoPipeline
from diffusers.utils import export_to_video
from botocore.config import Config
from app.core.config import settings
from sentiric.event.v1 import event_pb2
from google.protobuf.timestamp_pb2 import Timestamp

logger = structlog.get_logger()

class WanEngine:
    def __init__(self):
        self.pipe = None
        self.s3 = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT, aws_access_key_id=settings.S3_ACCESS_KEY, aws_secret_access_key=settings.S3_SECRET_KEY, config=Config(signature_version='s3v4'))

    def initialize(self):
        logger.info(f"Loading Wan2.1 from {settings.MODEL_ID}", event_id="MODEL_INIT")
        try:
            # Wan2.1 T2V 1.3B modelini 6GB VRAM'e sığdırmak için offload kullanıyoruz
            self.pipe = WanVideoPipeline.from_pretrained(settings.MODEL_ID, torch_dtype=torch.bfloat16).to(settings.DEVICE)
            self.pipe.enable_model_cpu_offload() 
            logger.info("Wan2.1 Expert Engine Ready.", event_id="MODEL_READY")
        except Exception as e:
            logger.error(f"Load Fail: {e}", event_id="MODEL_INIT_FAIL")

    async def generate_async(self, prompt: str, job_id: str, trace_id: str, tenant_id: str):
        logger.info("Starting Wan2.1 Render...", event_id="VIDEO_RENDER_START", trace_id=trace_id)
        path = f"/tmp/{job_id}.mp4"
        
        def render():
            # Düşük çözünürlük ve az frame ile hızlı üretim
            video = self.pipe(prompt=prompt, num_frames=21, height=480, width=832).frames[0]
            export_to_video(video, path, fps=15)
            
        try:
            await asyncio.to_thread(render)
            object_name = f"videos/{job_id}.mp4"
            await asyncio.to_thread(self.s3.upload_file, path, settings.S3_BUCKET, object_name)
            os.remove(path)
            
            s3_uri = f"s3://{settings.S3_BUCKET}/{object_name}"
            logger.info("Video uploaded", event_id="VIDEO_RENDER_SUCCESS", trace_id=trace_id, uri=s3_uri)
            
            # RabbitMQ Event
            conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with conn:
                ch = await conn.channel()
                ex = await ch.declare_exchange("sentiric_events", aio_pika.ExchangeType.TOPIC, durable=True)
                ts = Timestamp(); ts.GetCurrentTime()
                evt = event_pb2.MediaGenerationCompletedEvent(
                    event_type="media.generation.completed", trace_id=trace_id, job_id=job_id, 
                    tenant_id=tenant_id, media_type="video", success=True, result_uri=s3_uri, timestamp=ts)
                await ex.publish(aio_pika.Message(body=evt.SerializeToString(), content_type="application/protobuf"), routing_key="media.generation.completed")
                
        except Exception as e:
            logger.error(f"Wan2.1 Render failed: {e}", event_id="VIDEO_RENDER_FAIL", trace_id=trace_id)
        finally:
            torch.cuda.empty_cache()

wan_engine = WanEngine()