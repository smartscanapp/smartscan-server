import chromadb
from PIL import Image
from pydantic import BaseModel
from typing import Literal

from fastapi import FastAPI, UploadFile, File, Form, HTTPException,  WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool

from smartscan.types import ModelName
from smartscan.constants import SupportedFileTypes
from smartscan.utils import are_valid_files, get_files_from_dirs
from smartscan.indexer import FileIndexer
from smartscan.providers import MiniLmTextEmbedder, ClipImageEmbedder, DinoSmallV2ImageEmbedder, ClipTextEmbedder, ImageEmbeddingProvider, TextEmbeddingProvider, ClipImageEmbedder
from server.config import load_config, save_config
from server.indexer import FileIndexerWebSocketListener, FailMessage
from server.constants import  DB_DIR, SMARTSCAN_CONFIG_PATH, MODEL_PATHS

config = load_config(SMARTSCAN_CONFIG_PATH)

client = chromadb.PersistentClient(path=DB_DIR)

FileType = Literal['text', 'image', 'video']

# Unique name based on model and data type prevents embedding dimensions related errors
def get_collection(model_name: ModelName, type: FileType):
    return client.get_or_create_collection(
    name=f"{model_name}_{type}_collection",
    metadata={"description": f"Collection for {type}s"}
)

text_store = get_collection(config.text_encoder_model, 'text')
image_store = get_collection(config.image_encoder_model, 'image')
video_store = get_collection(config.image_encoder_model, 'video')

def get_image_encoder(name: ModelName) -> ImageEmbeddingProvider:
    if name == "dinov2-small":
        return DinoSmallV2ImageEmbedder(MODEL_PATHS[name])
    elif name == 'clip-vit-b-32-image':
        return ClipImageEmbedder(MODEL_PATHS[name])
    raise ValueError(f"Invalid model name: {name}")

def get_text_encoder(name: ModelName) -> TextEmbeddingProvider:
    if name == 'all-minilm-l6-v2':
        return MiniLmTextEmbedder(MODEL_PATHS[name])
    elif name == 'clip-vit-b-32-text':
        return ClipTextEmbedder(MODEL_PATHS[name])
    raise ValueError(f"Invalid model name: {name}")


image_encoder = get_image_encoder(config.image_encoder_model)
text_encoder = get_text_encoder(config.text_encoder_model)
image_encoder.init()
text_encoder.init()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

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
    if not are_valid_files(SupportedFileTypes.IMAGE, [query_image.filename]):
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


@app.post("/api/search/images")
async def search_images(query_image: UploadFile = File(...),threshold: float = Form(config.similarity_threshold)):
    return await _image_query(image_store, query_image, threshold)


@app.post("/api/search/videos")
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


@app.post("/api/search/docs")
async def search_documents(request: TextQueryRequest):
    return await _text_query(request, text_store)


def _filter(items: list[str], image_store: chromadb.Collection | None = None, text_store: chromadb.Collection| None = None,video_store: chromadb.Collection| None = None ) -> list[str]:
        image_ids = _get_exisiting_ids(image_store)
        text_ids = _get_exisiting_ids(text_store)
        video_ids = _get_exisiting_ids(video_store)
        exclude = set(image_ids) | set(text_ids) | set(video_ids)
        return [item for item in items if item not in exclude]
  
def _get_exisiting_ids (store: chromadb.Collection| None = None) -> list[str]:
        limit = 100
        offset = 0
        ids = []
        if not store:
             return ids
        
        while True:
            batch = store.get(limit=limit, offset=offset)
            if not batch['ids']:
                break
            ids.extend(batch['ids'])
            offset += limit
        return ids

async def _index( ws: WebSocket, allowed_exts: tuple[str], indexer: FileIndexer, image_store: chromadb.Collection | None = None, text_store: chromadb.Collection| None = None,video_store: chromadb.Collection| None = None):
    msg = await ws.receive_json()
    if msg.get("action") == "index":
        dirpaths = msg.get("dirs", [])
        files = get_files_from_dirs(dirpaths, allowed_exts=allowed_exts)
        filtered_files = _filter(files, image_store, text_store, video_store)
        await indexer.run(filtered_files)
        await ws.close()
    else: 
        await ws.send_json(FailMessage(error="invalid action").model_dump())
        await ws.close()
 


@app.websocket("/ws/index/docs")
async def index(ws: WebSocket):
    await ws.accept()

    listener = FileIndexerWebSocketListener(ws,store=text_store)
    indexer = FileIndexer(
        image_encoder=image_encoder,
        text_encoder=text_encoder,
        listener=listener,
    )

    try:
        await _index(ws, SupportedFileTypes.TEXT, indexer, text_store=text_store)
    except RuntimeError:
         print("Runtime Error")
    except WebSocketDisconnect:
        print("Client disconnected")


@app.websocket("/ws/index/images")
async def index(ws: WebSocket):
    await ws.accept()

    listener = FileIndexerWebSocketListener(ws,store=image_store)
    indexer = FileIndexer(
        image_encoder=image_encoder,
        text_encoder=text_encoder,
        listener=listener,
    )

    try:
        await _index(ws, SupportedFileTypes.IMAGE, indexer, image_store=image_store)
    except RuntimeError:
         print("Runtime Error")
    except WebSocketDisconnect:
        print("Client disconnected")


@app.websocket("/ws/index/videos")
async def index(ws: WebSocket):
    await ws.accept()

    listener = FileIndexerWebSocketListener(ws,store=video_store,)

    indexer = FileIndexer(
        image_encoder=image_encoder,
        text_encoder=text_encoder,
        listener=listener,
    )

    try:
        await _index(ws, SupportedFileTypes.VIDEO, indexer, video_store=video_store)
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

@app.get("/api/count/docs")
async def count_documents_collection():
    return await _count(text_store)

@app.get("/api/count/images")
async def count_image_collection():
    return await _count(image_store)

@app.get("/api/count/videos")
async def count_video_collection():
      return await _count(video_store)


async def _select_encoder(selected_model: ModelName, type: FileType):
    if selected_model is None:
        raise HTTPException(status_code=400, detail="Missing selected_model")
  
    try:
        if type == 'image' or type == 'video':
            global image_encoder
            image_encoder.close_session()
            image_encoder = get_image_encoder(selected_model)
            image_encoder.init()
            config.image_encoder_model = selected_model
        else:
            global text_encoder
            text_encoder.close_session()
            text_encoder = get_text_encoder(selected_model)
            text_encoder.init()
            config.text_encoder_model = selected_model
            global text_store
            text_store = get_collection(selected_model, 'text')
        
        if type == 'image':
            global image_store
            image_store = get_collection(selected_model, 'image')
        elif type == 'video':
            global video_store
            video_store = get_collection(selected_model, 'video')
            
        save_config(SMARTSCAN_CONFIG_PATH, config)         
    except Exception as _:
            raise HTTPException(status_code=500, detail="Error selecting model")

    return JSONResponse({"current_model": selected_model})


@app.post("/api/select_model/images")
async def update_model_for_image_search(selected_model: ModelName):
    return await _select_encoder(selected_model, 'image')

@app.post("/api/select_model/docs")
async def update_model_for_doc_search(selected_model: ModelName):
    return await _select_encoder(selected_model, 'text')


@app.post("/api/select_model/videos")
async def update_model_for_video_search(selected_model: ModelName):
    return await _select_encoder(selected_model, 'video')

