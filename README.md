# SmartScan Server

## Overview

SmartScan Server provides a local API for **file indexing** and **semantic search** across text, images, and videos. 

---


## Server Usage

Options:

* `[--port, -p] PORT` – Port to start the server (default: 8000)
* `[--workers, -w] WORKERS` – Number of worker processes (default: 0)

---

### Supported File Types

* **Images:** `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`
* **Text:** `.txt`, `.md`, `.rst`, `.html`, `.json`
* **Videos:** `.mp4`, `.mkv`, `.webm`

---

## API Reference 

| #  | Endpoint                   | Method    | Request                                                                              | Response                                           | Notes / Example                                                                      |
| -- | -------------------------- | --------- | ------------------------------------------------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1  | `/api/search/images`       | POST      | `multipart/form-data`: `query_image` (file, required), `threshold` (float, optional) | `{"results": ["id1", "id2"]}`                      | Search images. Example: `curl -F "query_image=@example.png" -F "threshold=0.75" ...` |
| 2  | `/api/search/videos`       | POST      | `multipart/form-data`: `query_image` (file, required), `threshold` (float, optional) | `{"results": ["vid1", "vid2"]}`                    | Search videos.                                                                       |
| 3  | `/api/search/docs`         | POST      | JSON: `{"query": "text", "threshold": 0.8}`                                          | `{"results": ["doc1", "doc2"]}`                    | Search text documents.                                                               |
| 4  | `/ws/index/docs`           | WebSocket | JSON messages: `{"action":"index","dirs":["/path"]}`                                 | Streaming WebSocket messages with indexing updates | Real-time text file indexing.                                                        |
| 5  | `/ws/index/images`         | WebSocket | JSON messages: `{"action":"index","dirs":["/path"]}`                                 | Streaming WebSocket messages with indexing updates | Real-time image indexing.                                                            |
| 6  | `/ws/index/videos`         | WebSocket | JSON messages: `{"action":"index","dirs":["/path"]}`                                 | Streaming WebSocket messages with indexing updates | Real-time video indexing.                                                            |
| 7  | `/api/count/docs`          | GET       | None                                                                                 | `{"count": 123}`                                   | Count items in text collection.                                                      |
| 8  | `/api/count/images`        | GET       | None                                                                                 | `{"count": 45}`                                    | Count items in image collection.                                                     |
| 9  | `/api/count/videos`        | GET       | None                                                                                 | `{"count": 30}`                                    | Count items in video collection.                                                     |
| 10 | `/api/select_model/images` | POST      | JSON: `{"selected_model": "clip-vit-b-32-image"}`                                    | `{"current_model": "clip-vit-b-32-image"}`         | Switch image encoder model.                                                          |
| 11 | `/api/select_model/docs`   | POST      | JSON: `{"selected_model": "all-minilm-l6-v2"}`                                       | `{"current_model": "all-minilm-l6-v2"}`            | Switch text encoder model.                                                           |
| 12 | `/api/select_model/videos` | POST      | JSON: `{"selected_model": "clip-vit-b-32-image"}`                                    | `{"current_model": "clip-vit-b-32-image"}`         | Switch video encoder model.                                                          |
