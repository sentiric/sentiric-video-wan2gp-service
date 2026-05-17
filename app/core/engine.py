# [ARCH-COMPLIANCE] SOP-01: Eksiksiz Teslimat
import torch, gc, asyncio, os, uuid, structlog
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.schedulers import UniPCMultistepScheduler
from diffusers.utils import export_to_video
from app.core.config import settings
from app.core.integrations import S3Uploader, RMQPublisher

logger = structlog.get_logger()

class WanEngine:
    def __init__(self):
        self.pipe = None
        self.semaphore = asyncio.Semaphore(1)
        self.s3_uploader = S3Uploader()
        self.rmq_publisher = RMQPublisher()

    def initialize(self):
        logger.info(f"Loading Wan2.1-1.3B: {settings.MODEL_ID}", event_id="MODEL_INIT")
        try:
            # Wan2.1 için önerilen VAE ve Scheduler ayarları
            # 480P için flow_shift=3.0 altın kuraldır.
            vae = AutoencoderKLWan.from_pretrained(settings.MODEL_ID, subfolder="vae", torch_dtype=torch.float32)
            scheduler = UniPCMultistepScheduler(
                prediction_type='flow_prediction', 
                use_flow_sigmas=True, 
                num_train_timesteps=1000, 
                flow_shift=3.0 
            )

            self.pipe = WanPipeline.from_pretrained(
                settings.MODEL_ID, 
                vae=vae, 
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True
            )
            self.pipe.scheduler = scheduler

            if settings.DEVICE == "cuda":
                # 6GB VRAM kurtarıcısı
                self.pipe.enable_sequential_cpu_offload()
                self.pipe.vae.enable_slicing()
                self.pipe.vae.enable_tiling()
                
            logger.info("Wan2.1 Expert Engine Ready.", event_id="MODEL_READY")
        except Exception as e:
            logger.error(f"Model Load Fail: {str(e)}", event_id="MODEL_INIT_FAIL")
            self.pipe = None

    async def generate_async(self, prompt: str, job_id: str, trace_id: str, tenant_id: str):
        if self.pipe is None: return

        async with self.semaphore:
            logger.info(f"Wan2.1 Rendering: {prompt[:50]}...", event_id="VIDEO_RENDER_START", trace_id=trace_id)
            path = f"/tmp/{job_id}.mp4"
            
            def render():
                # 480P Wan2.1 Standartları (832x480)
                # num_frames: 81 (5 saniye) çok ağır gelebilir, 25 (1.5 sn) ile başlıyoruz.
                with torch.inference_mode():
                    output = self.pipe(
                        prompt=prompt,
                        num_frames=25, 
                        num_inference_steps=25,
                        height=480,
                        width=832,
                        guidance_scale=6.0, # 1.3B için önerilen değer 6.0'dır
                        output_type="np"
                    )
                export_to_video(output.frames[0], path, fps=15)
            
            try:
                await asyncio.to_thread(render)
                s3_uri = await asyncio.to_thread(self.s3_uploader.upload_file, path, job_id, trace_id)
                if os.path.exists(path): os.remove(path)
                
                await self.rmq_publisher.publish_event("media.generation.completed", trace_id, tenant_id, job_id, True, s3_uri)
                logger.info("Video Success", trace_id=trace_id, uri=s3_uri)
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Render failed: {err_msg}", event_id="VIDEO_RENDER_FAIL", trace_id=trace_id)
                await self.rmq_publisher.publish_event("media.generation.failed", trace_id, tenant_id, job_id, False, "", err_msg)
            finally:
                if settings.DEVICE == "cuda":
                    gc.collect(); torch.cuda.empty_cache()

wan_engine = WanEngine()