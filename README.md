# SmartScan Server

## Overview

SmartScan Server powers the SmartScan Desktop app (coming soon) by providing a local API for **file indexing** and **semantic search** across text, images, and videos. 

---

## Installation

### Prerequisites

* Python 3.10+

### Installation Steps

Install via pip:

```bash
pip install git+https://github.com/smartscanapp/smartscan-server.git
```

---

## Server Usage

Run the server locally:

```bash
smartscan --server [OPTIONS]
```

Options:

* `[--port, -p] PORT` – Port to start the server (default: 8000)
* `[--workers, -w] WORKERS` – Number of worker processes (default: 0)

---

## Features

* **Semantic Search**

  * Search **text** using MiniLM or CLIP embeddings.
  * Search **images** using CLIP or DinoV2 embeddings.
  * Search **videos** via frame-based image embeddings.

* **WebSocket-Based Indexing**

  * Index files in directories in real-time.
  * Supports stopping and monitoring progress via WebSocket.

* **Collections Management**

  * Separate collections for **text**, **images**, and **videos**.
  * Query and count items in each collection.

* **Extensible Model Support**

  * Easily switch or add embedding models via configuration.

---

## Supported File Types

* **Images:** `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`
* **Text:** `.txt`, `.md`, `.rst`, `.html`, `.json`
* **Videos:** `.mp4`, `.mkv`, `.webm`

---