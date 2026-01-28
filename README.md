# Beyond Classification: Zero-Shot Threat Attribution for Open-World APTs via Semantic Graph Alignment

This repository contains the source code and datasets for the paper “Beyond Classification: Zero-Shot Threat Attribution for Open-World APTs via Semantic Graph Alignment”

## Availability Status

To uphold the double-blind review process and data privacy regulations, this repository currently contains the limit content.

We are currently: 1.  **Sanitizing the Dataset:** Removing sensitive indicators (IOCs) and proprietary tags. 2.  **Decoupling APIs:** Abstracting the internal ElasticSearch and LLM connectors for public use.

The complete source code and datasets will be released upon paper acceptance.

## Environment

We use **[pixi](https://prefix.dev/)** to ensure strict reproducibility of our experimental environment. You do not need to manually install Python, CUDA, or PyTorch. 

1. Prerequisites Install Pixi (if not already installed): 

   ```bash
   curl -fsSL [https://pixi.sh/install.sh](https://pixi.sh/install.sh) | bash
   ```

2. Clone this repository and install the environment with a single command. This will fetch all dependencies (including Python and system-level libraries) defined in `pixi.lock`.

   ```
   pixi install
   ```

   



