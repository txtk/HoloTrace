# Beyond Classification: Zero-Shot Threat Attribution for Open-World APTs via Semantic Graph Alignment

This repository contains the source code and datasets for the paper **“Beyond Classification: Zero-Shot Threat Attribution for Open-World APTs via Semantic Graph Alignment”**.

## Description

**HoloTrace** is a zero-shot, open-set threat attribution framework designed to overcome the limitations of traditional closed-set classification in Cyber Threat Intelligence (CTI). By reformulating attribution as an entity-level semantic alignment problem, HoloTrace projects threat graphs into a four-layer pyramid structure and utilizes a frozen Large Language Model (LLM) for bottom-up denoising. This approach effectively maps heterogeneous behaviors into a unified semantic space, enabling robust identification of long-tail actors and previously unseen threats without requiring predefined labels.

This work also introduces **HEAA**, a benchmark that evaluates alignment robustness, quantifying the distributional properties and discriminative power of IoCs, TTPs, and malware entities in attribution scenarios.

## Project Structure

The repository is organized into the following logical components:

```text
.
├── alignment/       # Core Logic: Semantic alignment algorithms & Zero-shot attribution models
├── CeleryManage/    # Task Queue: Configuration and control scripts for Celery workers
├── data/            # Datasets: Sanitized APT reports and graph schema definitions (HEAA Benchmark)
├── envs/            # Infrastructure: Docker-compose setups for Redis, RabbitMQ, and ElasticSearch
├── prompt/          # LLM Engineering: Prompt templates for entity extraction and reasoning
└── utils/           # Utilities: Helper functions, API connectors, and data pre-processors
```

### Component Details

- **`alignment/`**: Contains the main implementation of the HoloTrace framework, including graph node embedding, pyramid projection, and similarity calculation modules.
- **`CeleryManage/`**: Manages the distributed task queue system. It includes the Celery application initialization, worker configuration, and scripts to handle asynchronous graph processing tasks.
- **`data/`**: Stores the input data required for experiments. Sensitive fields in the raw APT reports have been sanitized to uphold privacy regulations.
- **`envs/`**: Configuration files for setting up the external runtime environment. Use the files here to quickly spin up the required services via Docker.
- **`prompt/`**: Contains the specific prompt designs used to guide the LLM in extracting structured threat intelligence and performing evidence-driven decision-making.
- **`utils/`**: Shared libraries for data loading, logging, and interfacing with backend services (e.g., ElasticSearch connector).

## Environment Setup

We use **[pixi](https://prefix.dev/)** to ensure strict reproducibility of our experimental environment. You do not need to manually install Python, CUDA, or PyTorch.

### 1. Prerequisites

**Install Pixi** (if not already installed):

Bash

```
curl -fsSL [https://pixi.sh/install.sh](https://pixi.sh/install.sh) | bash
```

**Infrastructure Services**: Before running the pipeline, ensure the following backend services are available and reachable. You can verify the configurations in the `envs/` directory:

- **Redis**: Used for task queuing and caching.
- **RabbitMQ**: Used as the message broker for Celery tasks.
- **ElasticSearch (ES)**: Used for storing and querying semantic graph data.

### 2. Install Project Dependencies

Clone this repository and install the environment. This will fetch all dependencies (including Python and system-level libraries) defined in `pixi.lock`.

Bash

```
pixi install
```

## Running the Project

The system relies on a distributed task queue for processing and a main alignment module for threat attribution.

### Step 1: Start the Worker

Start the Celery worker to handle background tasks and graph processing:

Bash

```
pixi run celery
```

### Step 2: Run Semantic Alignment

Execute the core zero-shot threat attribution and graph alignment logic:

Bash

```
pixi run alignment
```

> **Note**: Please ensure your configuration file (e.g., `.env` or `config.yaml`) is correctly updated with the host addresses and credentials for your Redis, RabbitMQ, and ElasticSearch instances before running the commands.
