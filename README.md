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

## API Reference 

| #  | Endpoint                       | Method    | Request                                                                              | Response                                           | Notes / Example                                                                      |
| -- | ------------------------------ | --------- | ------------------------------------------------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1  | `/api/search/image`            | POST      | `multipart/form-data`: `query_image` (file, required), `threshold` (float, optional) | `{"results": ["id1", "id2"]}`                      | Search images. Example: `curl -F "query_image=@example.png" -F "threshold=0.75" ...` |
| 2  | `/api/search/video`            | POST      | `multipart/form-data`: `query_image` (file, required), `threshold` (float, optional) | `{"results": ["vid1", "vid2"]}`                    | Search videos.                                                             |
| 3  | `/api/search/text`             | POST      | JSON: `{"query": "text", "threshold": 0.8}`                                          | `{"results": ["doc1", "doc2"]}`                    | Search text documents.                                                               |
| 4  | `/ws/index`                    | WebSocket | JSON messages: `{"action":"index","dirs":["/path"]}` or `{"action":"stop"}`          | Streaming WebSocket messages with indexing updates | Real-time file indexing.                                                             |
| 5  | `/api/collections/text/count`  | GET       | None                                                                                 | `{"count": 123}`                                   | Count items in text collection.                                                      |
| 6  | `/api/collections/image/count` | GET       | None                                                                                 | `{"count": 45}`                                    | Count items in image collection.                                                     |
| 7  | `/api/collections/video/count` | GET       | None                                                                                 | `{"count": 30}`                                    | Count items in video collection.                                                     |
| 8  | `/api/select_model/image`      | POST      | JSON: `{"selected_model": "clip-vit-b-32-image"}`                                    | `{"current_model": "clip-vit-b-32-image"}`         | Switch image encoder model.                                                          |
| 9  | `/api/select_model/text`       | POST      | JSON: `{"selected_model": "all-minilm-l6-v2"}`                                       | `{"current_model": "all-minilm-l6-v2"}`            | Switch text encoder model.                                                           |
| 10 | `/api/select_model/video`      | POST      | JSON: `{"selected_model": "clip-vit-b-32-image"}`                                    | `{"current_model": "clip-vit-b-32-image"}`         | Switch video encoder model.                                                          |