import chromadb
from PIL import Image
from pydantic import BaseModel

from fastapi import FastAPI, UploadFile, File, Form, HTTPException,  WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool

from smartscan.utils import are_valid_files, get_files_from_dirs
from smartscan.indexer import FileIndexer
from smartscan.providers import MiniLmTextEmbedder, ClipImageEmbedder, DinoSmallV2ImageEmbedder, ClipTextEmbedder, ImageEmbeddingProvider, TextEmbeddingProvider, ClipImageEmbedder
from server.config import load_config
from server.indexer import FileIndexerWebSocketListener
from server.constants import  DB_DIR, SMARTSCAN_CONFIG_PATH, MODEL_REGISTRY, MODEL_PATHS
from smartscan.constants import ModelName

config = load_config(SMARTSCAN_CONFIG_PATH)

client = chromadb.PersistentClient(path=DB_DIR)
text_store = client.get_or_create_collection(
    name=f"{config.text_encoder_model}_text_collection",
    metadata={"description": "Collection for text documents"}
)
image_store = client.get_or_create_collection(
    name=f"{config.image_encoder_model}_image_collection",
    metadata={"description": "Collection for images"}
) 
video_store = client.get_or_create_collection(
    name=f"{config.image_encoder_model}_video_collection",
    metadata={"description": "Collection for videos"}
)

def get_image_encoder(name: ModelName) -> ImageEmbeddingProvider:
    if name == MODEL_REGISTRY["dinov2-small"]:
        return DinoSmallV2ImageEmbedder(MODEL_PATHS[name])
    elif name == MODEL_REGISTRY['clip-vit-b-32-image']:
        return ClipImageEmbedder(MODEL_PATHS[name])
    raise ValueError(f"Invalid model name: {name}")

def get_text_encoder(name: str) -> TextEmbeddingProvider:
    if name == MODEL_REGISTRY['all-minilm-l6-v2']:
        return MiniLmTextEmbedder(MODEL_PATHS[name])
    elif name == MODEL_REGISTRY['clip-vit-b-32-text']:
        return ClipTextEmbedder(MODEL_PATHS[name])
    raise ValueError(f"Invalid model name: {name}")


image_encoder = get_image_encoder(config.image_encoder_model)
text_encoder = get_text_encoder(config.text_encoder_model)
image_encoder.init()
text_encoder.init()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXT = ('png', 'jpg', 'jpeg', 'bmp', 'webp')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
    max_age=3600,
)

async def _image_query(store: chromadb.Collection, query_image: UploadFile = File(...), threshold: float = Form(config.similarity_threshold)):
    if query_image.filename is None:
        raise HTTPException(status_code=400, detail="Missing query_image")
    if not are_valid_files(ALLOWED_EXT, [query_image.filename]):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        image = Image.open(query_image.file)
        query_embedding = await run_in_threadpool(image_encoder.embed, image)

    except Exception as _:
            raise HTTPException(status_code=500, detail="Error generating embedding")

    try:
          results = store.query(query_embeddings=[query_embedding])
    except Exception as _:
            raise HTTPException(status_code=500, detail="Error querying database")

    ids = [id_ for id_, distance in zip(results['ids'][0], results['distances'][0]) if distance <= threshold]
    
    return JSONResponse({"results": ids})


@app.post("/api/search/image")
async def search_images(query_image: UploadFile = File(...),threshold: float = Form(config.similarity_threshold)):
    return await _image_query(image_store, query_image, threshold)


@app.post("/api/search/video")
async def search_videos(query_image: UploadFile = File(...),threshold: float = Form(config.similarity_threshold)):
    return await _image_query(video_store, query_image, threshold)


class TextQueryRequest(BaseModel):
    query: str
    threshold: float = config.similarity_threshold


async def _text_query(request: TextQueryRequest, store: chromadb.Collection):
    if request.query is None:
        raise HTTPException(status_code=400, detail="Missing query text")
  
    try:
        query_embedding = await run_in_threadpool(text_encoder.embed, request.query)
    except Exception as _:
            raise HTTPException(status_code=500, detail="Error generating embedding")

    try:
          results = store.query(query_embeddings=[query_embedding])
    except Exception as _:
            raise HTTPException(status_code=500, detail="Error querying database")

    ids = [id_ for id_, distance in zip(results['ids'][0], results['distances'][0]) if distance <= request.threshold]

    return JSONResponse({"results": ids})


@app.post("/api/search/text")
async def search_documents(request: TextQueryRequest):
    return await _text_query(request, text_store)


@app.websocket("/ws/index")
async def index(ws: WebSocket):
    await ws.accept()

    listener = FileIndexerWebSocketListener(
        ws,
        image_store=image_store,
        text_store=text_store,
        video_store=video_store,
        )
    
    indexer = FileIndexer(
        image_encoder=image_encoder,
        text_encoder=text_encoder,
        listener=listener,
    )

    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("action") == "index":
                dirpaths = msg.get("dirs", [])
                allowed_exts = indexer.valid_img_exts + indexer.valid_txt_exts + indexer.valid_vid_exts
                files = get_files_from_dirs(dirpaths, allowed_exts=allowed_exts)
                await indexer.run(files)
            elif msg.get("action") == "stop":
                break
    except RuntimeError:
         print("Runtime Error")
    except WebSocketDisconnect:
        print("Client disconnected")


async def _count(store: chromadb.Collection):
    try:
        count = await run_in_threadpool(store.count)
    except Exception as _:
            raise HTTPException(status_code=500, detail="Error counting items in collection")
    return JSONResponse({"count": count})

@app.get("/api/collections/text/count")
async def count_documents_collection():
    return await _count(text_store)

@app.get("/api/collections/image/count")
async def count_image_collection():
    return await _count(image_store)

@app.get("/api/collections/video/count")
async def count_video_collection():
      return await _count(video_store)