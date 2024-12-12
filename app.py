from fastapi import FastAPI, HTTPException, BackgroundTasks
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

load_dotenv()
app = FastAPI()
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

def generate_completion(prompt: str) -> str:
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
        logger.error(f"Ollama generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        future = producer.send('summarization_requests', message)
        await asyncio.get_event_loop().run_in_executor(None, future.get, 60)
    except Exception as e:
        logger.error(f"Kafka send error: {e}")

@app.post("/summarize")
async def summarize_text(request: SummaryRequest, background_tasks: BackgroundTasks):
    cache_key = hashlib.md5(f"{request.text}{request.style}{request.max_length}{request.bullet_points}".encode()).hexdigest()
    
    if cache_key in summary_cache:
        return summary_cache[cache_key]
    
    prompt = f"""{STYLE_PROMPTS.get(request.style, STYLE_PROMPTS["formal"])}

Please start your response by stating "Here is a {request.max_length}-word summary:"

Critical Instructions:
- Only use information explicitly stated in the provided text
- Do not add any external information or assumptions
- Do not make inferences beyond what is directly supported by the text
- Maintain factual accuracy without embellishment
- Stick strictly to the content provided

Guidelines:
- Maximum length: {request.max_length} words
- Format: {"bullet points" if request.bullet_points else "paragraph"}
- Preserve critical information
- Remove redundancy

Text to summarize:
{request.text}"""
    
    summary = generate_completion(prompt)
    result = {"summary": summary, "style": request.style}
    summary_cache[cache_key] = result
    
    # Send to Kafka in background
    if hasattr(app.state, 'kafka_producer'):
        background_tasks.add_task(
            send_to_kafka,
            app.state.kafka_producer,
            {
                'text': request.text,
                'style': request.style,
                'timestamp': time.time(),
                'cache_key': cache_key
            }
        )
    
    return result

@app.on_event("startup")
async def startup_event():
    app.state.kafka_producer = await init_kafka()
    logger.info("Kafka producer initialized")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, 'kafka_producer'):
        app.state.kafka_producer.close()
        logger.info("Kafka producer closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
