import grpc, os, uuid, time, random
from sentiric.video.v1 import gateway_pb2, gateway_pb2_grpc

PROMPTS = [
    "A white cat wearing sunglasses sits on a surfboard at a tropical beach, fluffy fur, cinematic lighting",
    "Cinematic shot of a steampunk clock tower interior, gears rotating, brass textures, dust motes in sunbeams",
    "Two cute robots playing chess in a futuristic park, neon trees in background, detailed digital art",
    "A slow motion shot of coffee pouring into a glass of milk, swirling cream, macro photography, 4k",
    "An epic dragon flying over a snow-covered mountain peak, wings flapping, realistic textures"
]

def run_test():
    base_cert_dir = "../sentiric-certificates/certs"
    with open(os.path.join(base_cert_dir, "ca.crt"), "rb") as f: ca = f.read()
    with open(os.path.join(base_cert_dir, "video-wan2gp-service-chain.crt"), "rb") as f: cert = f.read()
    with open(os.path.join(base_cert_dir, "video-wan2gp-service.key"), "rb") as f: key = f.read()
    
    creds = grpc.ssl_channel_credentials(ca, key, cert)
    with grpc.secure_channel("localhost:16121", creds) as channel:
        stub = gateway_pb2_grpc.VideoGatewayServiceStub(channel)
        prompt = random.choice(PROMPTS)
        print(f"🎬 Wan2.1 Talebi Gönderiliyor: '{prompt}'")
        
        response = stub.SubmitVideoJob(gateway_pb2.SubmitVideoJobRequest(
            tenant_id="test-tenant", trace_id=str(uuid.uuid4()),
            prompt=prompt, preferred_model="wan2.1-1.3b"
        ))
        print(f"✅ Kabul Edildi | Job ID: {response.job_id}")

if __name__ == "__main__":
    run_test()