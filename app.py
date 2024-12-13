from fastapi import FastAPI, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.gzip import GZipMiddleware
from cachetools import TTLCache
from kafka import KafkaProducer
from kafka.errors import KafkaError
from pydantic import BaseModel
from dotenv import load_dotenv
import hashlib
import ollama
import logging
import asyncio
import json
import time
import os
from contextlib import asynccontextmanager
from shared.base_service import BaseService
from circuitbreaker import circuit
import uuid

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.kafka_producer = await init_kafka()
    logger.info("Kafka producer initialized")
    yield
    # Shutdown
    if hasattr(app.state, 'kafka_producer'):
        app.state.kafka_producer.close()
        logger.info("Kafka producer closed")

service = BaseService("text_summarizer")
app = service.app
app.lifespan = lifespan  # Set lifespan for the service app
app.add_middleware(GZipMiddleware, minimum_size=1000)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache configuration
summary_cache = TTLCache(maxsize=100, ttl=3600)

class SummaryRequest(BaseModel):
    text: str
    style: str = "formal"
    max_length: int = 500
    bullet_points: bool = False

class SummaryStatus(BaseModel):
    id: str
    status: str
    result: dict = None
    error: str = None

summary_status = {}

STYLE_PROMPTS = {
    "formal": """I will now provide a formal academic summary:

Provide a formal academic summary that:
- Uses scholarly language and precise terminology
- Maintains objective, third-person perspective
- Emphasizes key research findings and methodologies
- Structures information in a logical, systematic manner
- Avoids colloquialisms and informal expressions""",

    "informal": """I will now provide a conversational summary:

Create a conversational summary that:
- Uses everyday language and natural expressions
- Explains concepts as if talking to a friend
- Includes relatable examples where appropriate
- Breaks down complex ideas into simple terms
- Maintains a friendly, approachable tone""",

    "technical": """I will now provide a technical summary:

Generate a technical summary that:
- Focuses on specifications, metrics, and technical details
- Preserves essential technical terminology
- Outlines system architectures or methodologies
- Includes relevant technical parameters and measurements
- Maintains precision in technical descriptions""",

    "executive": """I will now provide an executive summary:

Provide an executive summary that:
- Leads with key business implications and ROI
- Highlights strategic insights and recommendations
- Focuses on actionable conclusions
- Quantifies impacts and outcomes
- Structures information in order of business priority""",

    "creative": """I will now provide a creative narrative summary:

Craft an engaging narrative summary that:
- Uses vivid analogies and metaphors
- Incorporates storytelling elements
- Creates memorable visual descriptions
- Makes complex ideas relatable through creative comparisons
- Maintains reader engagement through varied language"""
}

@circuit(failure_threshold=5, recovery_timeout=60)
def generate_completion(prompt: str) -> str:
    with service.request_latency.time():
        try:
            client = ollama.Client(host=os.getenv('OLLAMA_API_URL', 'http://ollama:11434'))
            response = client.generate(
                model=os.getenv('MODEL_NAME', 'llama3.1:3b'),
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_ctx': 4096,
                    'num_predict': 2048,
                    'num_gpu': int(os.getenv('NUM_GPU', 1)),
                    'num_thread': int(os.getenv('NUM_THREAD', 4))
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Circuit breaker: {str(e)}")
            raise

async def init_kafka():
    try:
        return KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
    except KafkaError as e:
        logger.error(f"Kafka initialization error: {e}")
        return None

async def send_to_kafka(producer, message):
    if not producer:
        return
    try:
        future = producer.send('summarizer_requests', message)  # Changed topic name
        await asyncio.get_event_loop().run_in_executor(None, future.get, 60)
    except Exception as e:
        logger.error(f"Kafka send error: {e}")

api_router = APIRouter(prefix="/api/v1")

@api_router.post("/summarize")
async def summarize_text(request: SummaryRequest, background_tasks: BackgroundTasks):
    request_id = str(uuid.uuid4())
    summary_status[request_id] = {"status": "processing"}
    
    try:
        service.request_count.inc()
        cache_key = hashlib.md5(f"{request.text}{request.style}{request.max_length}{request.bullet_points}".encode()).hexdigest()
        
        if cache_key in summary_cache:
            result = summary_cache[cache_key]
            summary_status[request_id] = {"status": "completed", "result": result}
            return {"id": request_id, "status": "completed", "result": result}
        
        background_tasks.add_task(process_summary, request, request_id, cache_key)
        return {"id": request_id, "status": "processing"}
        
    except Exception as e:
        summary_status[request_id] = {"status": "error", "error": str(e)}
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/summarize/status/{request_id}")
async def get_summary_status(request_id: str):
    if request_id not in summary_status:
        raise HTTPException(status_code=404, detail="Summary request not found")
    
    return summary_status[request_id]

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        workers=multiprocessing.cpu_count(),
        log_level="info"
    )
