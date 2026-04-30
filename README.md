# Beyond Classification: Threat Attribution for APTs via Entity-Level Semantic Alignment

This repository contains the source code and datasets for the paper **"Beyond Classification: Threat Attribution for APTs via Entity-Level Semantic Alignment"**.

## Introduction

**HoloTrace** is a zero-shot, open-set threat attribution framework designed to overcome the limitations of traditional classification in Cyber Threat Intelligence (CTI).

HoloTrace reformulates the attribution problem as an **entity-level semantic alignment** task. It projects threat graphs into a four-layer pyramid structure and uses a frozen Large Language Model (LLM) to denoise from the bottom up. This approach maps heterogeneous behaviors into a unified semantic space, enabling robust identification of long-tail attackers and unseen threats without the need for predefined labels.

This work also proposes the **HEAA Benchmark** to evaluate alignment robustness, quantifying the distribution characteristics and distinguishability of IoCs, TTPs, and malware entities in attribution scenarios.

## Data Availability

This repository provides the processed graph files used in the experiments, which are sufficient for running the semantic alignment and evaluation pipeline described in the paper.

The original raw CTI files are not redistributed due to copyright and redistribution restrictions, potential security sensitivity, and raw corpus size constraints. As a result, the full raw-to-graph reconstruction process cannot be reproduced from the complete original corpus in this public release.

To support transparency, this repository includes format and construction examples for HEAA-style data in `src/data/dataset/raw_example/`. Knowledge base data examples are provided in `src/data/raw_data/json/knowledge_base_example/`. These examples illustrate the expected data structure and construction process, but they are not the complete raw corpus.

The main released data artifacts are organized as follows:

*   **Processed graph files**: `src/data/dataset/heaa_random/` and `src/data/dataset/heaa_time/`.
*   **HEAA construction examples**: `src/data/dataset/raw_example/`.
*   **Knowledge base examples**: `src/data/raw_data/json/knowledge_base_example/`.
*   **Evaluation outputs**: available under the corresponding `traditional_save/` directories.

## Project Architecture

The project source code located in `src/` is organized into several key modules:

*   **`alignment/`**: Contains the core business logic for the semantic alignment process. This includes sub-modules for evaluation (`eval`), candidate matching (`match`), data preparation (`prepare`), and entity profiling (`profile`).
*   **`CeleryManage/`**: Implements the distributed task management system using Celery. It is divided into `scheduler` for task dispatching and `worker` for executing asynchronous graph processing tasks.
*   **`models/`**: Defines data models for interacting with databases (Neo4j, PostgreSQL) and abstracts interactions with various Large Language Models (LLMs) such as GLM and Qwen.
*   **`utils/`**: Provides shared utility functions for database operations (`database`), vector calculations (`vector`), string processing, and Neo4j graph interactions.
*   **`config/`** & **`envs/`**: Manages application settings and environment variables for different deployment stages (Development, Production, Test).

## Environment Setup

We use [pixi](https://pixi.sh/) to ensure strict reproducibility of the experimental environment. You do not need to manually install Python, CUDA, or PyTorch.

### 1. Prerequisites

**Install Pixi** (if not already installed):

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

**Infrastructure Services**:

Before running the pipeline, ensure the following backend services are available and accessible. You can check the configuration in `src/envs/`.

*   **Redis**: Used for task queuing and caching.
*   **RabbitMQ**: Message broker for Celery tasks.
*   **ElasticSearch (ES)**: Used for storing and querying semantic graph data.
*   **LLM API Key**: Configure relevant LLM service credentials.

### 2. Install Dependencies

Clone this repository and install the environment. This process pulls all dependencies defined in `pixi.lock` (including Python and system-level libraries).

```bash
pixi install
```

## Running the Project

The system relies on a distributed task queue for processing, with the main alignment module performing the threat attribution.

**Note**: Before running commands, ensure your configuration files (e.g., `src/envs/base.env`) are correctly updated with host addresses and credentials for Redis, RabbitMQ, and ElasticSearch.

### Step 1: Start Worker

Start the Celery worker to handle background tasks and graph processing:

```bash
pixi run celery
```

### Step 2: Run Semantic Alignment

Execute the core zero-shot threat attribution and graph alignment logic:

```bash
pixi run alignment
```
