# English Text Summarization Microservice

This is a microservice that summarizes English text using a Groq-hosted AI model. Currently, the Llama 80B model is being used for its performance, though the final model may vary. The service is designed to be deployed in a Docker container for easy integration into larger microservices architectures.

## Features

- **Text Summarization**: Summarizes English text using the Groq-hosted AI model.
- **Dockerized**: Easily deployable using Docker. (WIP)
- **Scalable**: Suitable for use in a microservices architecture, supporting Kafka or REST API for communication. (WIP)
- **Model**: Currently using Llama 80B for high-performance summarization. (WIP)

## Architecture

The service exposes an API endpoint for summarizing English text via HTTP POST requests. It also supports Kafka message consumption and production, making it suitable for event-driven architectures. (WIP)

- **Input**: English text.
- **Output**: Summarized text.
- **Model**: Groq-hosted model (currently Llama 80B).

## Requirements

Read requirements.txt

## Installation

**Coming soon.** Instructions for setting up and running the service will be added here.

## License 

This Project is under the MIT License, Read the LICENSE file for more information.
