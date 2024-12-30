# English Text Summarization Microservice

A high-performance microservice that leverages AI models through ollama to provide intelligent text summarization capabilities. The service is containerized and designed to work within a microservices architecture, supporting both REST API and Kafka-based communication.


## Features

- **Advanced Text Summarization**: Utilizes state-of-the-art AI models for accurate and contextual text summarization
- **Multiple Summarization Styles**:
  - Formal (academic/professional)
  - Informal (conversational)
  - Technical (specification-focused)
  - Executive (business-oriented)
  - Creative (narrative style)
- **Flexible Output Options**:
  - Configurable summary length
  - Bullet point or paragraph format
  - Cache support for improved performance
- **Enterprise Integration**:
  - REST API endpoints
  - Kafka message streaming support
  - Docker containerization
  - Horizontal scalability

## Technical Architecture

### Components
- **FastAPI Backend**: High-performance asynchronous API
- **Kafka Integration**: Event-driven architecture support
- **Docker Containerization**: Easy deployment and scaling
- **Caching Layer**: TTL-based caching for improved performance
- **AI Model**: ollama-hosted Llama model
- **Transformers Model**: Using a model from HuggingFace

### System Requirements
- Python 3.9+
- Docker and Docker Compose
- 4GB RAM minimum
- 2 CPU cores minimum


## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YoussefAlkent Text_Summerizer.git
   cd text-summarizer
   ```
   
2. **Environment Setup**
   ```bash
   # Create and edit .env file
   cp .env.example .env
   
   # Edit .env with your configurations:
   OLLAMA_API_URL=http://localhost:11434
   MODEL_NAME=llama3.2:3b
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   ```

3. **Docker Deployment**
   ```bash
   docker-compose up -d
   ```

4. **Verify Installation**
   ```bash
   curl http://localhost:8000/health
   ```

## API Usage

### REST Endpoint

POST `/summarize`

Request Body:
```json
{
    "text": "Your text to summarize here...",
    "style": "formal",
    "max_length": 500,
    "bullet_points": false
}
```

Available Styles:
- `formal` (default)
- `informal`
- `technical`
- `executive`
- `creative`

Example:
```bash
curl -X POST http://localhost:8000/summarize \
     -H "Content-Type: application/json" \
     -d '{"text": "Your text here", "style": "formal"}'
```

### Kafka Integration

Topics:
- `summarization_requests`: Input requests
- `summarization_results`: Summarization results

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OLLAMA_API_URL | ollama API endpoint | http://ollama:11434 |
| MODEL_NAME | AI model to use | llama3.2:3b |
| KAFKA_BOOTSTRAP_SERVERS | Kafka servers | kafka:9092 |
| WORKERS | Number of worker processes | 4 |

### Resource Limits

Docker container resources are configurable in `docker-compose.yml`:
- CPU: 1-2 cores
- Memory: 2-4GB

## Monitoring and Maintenance

### Health Checks
- REST API endpoint: `/health`
- Kafka health check: Built into docker-compose
- Zookeeper health check: Included in deployment

### Logging
- Application logs: Available through Docker logs
- Kafka logs: Stored in mounted volumes
- Request logging: Enabled by default

## Development

### Local Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

### Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please open an issue in the GitHub repository.
