from numpy import ndarray
from fastapi import WebSocket
from pydantic import BaseModel
from typing import Literal
from starlette.websockets import WebSocketState

from chromadb import Collection
from smartscan.utils import are_valid_files
from smartscan.processor import ProcessorListener

class ProgressMessage(BaseModel):
    type: Literal["progress"] = "progress"
    progress: float

class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    error: str
    item: str

class FailMessage(BaseModel):
    type: Literal["fail"] = "fail"
    error: str

class CompleteMessage(BaseModel):
    type: Literal["complete"] = "complete"
    total_processed: int
    time_elapsed: float

class FileIndexerWebSocketListener(ProcessorListener[str, tuple[str, ndarray]]):
    def __init__(
            self, 
            ws: WebSocket,
            image_store: Collection,
            text_store: Collection,
            video_store: Collection, 
                 ):
        self.ws = ws
        self.image_store = image_store
        self.text_store = text_store
        self.video_store = video_store
        self.valid_img_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
        self.valid_txt_exts = ('.txt', '.md', '.rst', '.html', '.json')
        self.valid_vid_exts = ('.mp4', '.mkv', '.webm')


    async def on_progress(self, progress):
        if self.ws.client_state == WebSocketState.CONNECTED:
            try:
                await self.ws.send_json(ProgressMessage(progress=progress).model_dump())  
            except RuntimeError:
                pass      
    
    async def on_fail(self, result):
        if self.ws.client_state == WebSocketState.CONNECTED:
            try:
                await self.ws.send_json(FailMessage(error=str(result.error)).model_dump())
            except RuntimeError:
                pass

    async def on_error(self, e, item):
        if self.ws.client_state == WebSocketState.CONNECTED:
            try:
                await self.ws.send_json(ErrorMessage(error=str(e), item=item).model_dump())
            except RuntimeError:
                pass

    async def on_complete(self, result):
        if self.ws.client_state == WebSocketState.CONNECTED:
            try:
                await self.ws.send_json(CompleteMessage(total_processed=result.total_processed, time_elapsed=result.time_elapsed).model_dump())
            except RuntimeError:
                pass

    async def on_batch_complete(self, batch):
        if len(batch) <= 0:
            return
        partitions = { "image": ([], []), "text": ([], []), "video": ([], [])}

        for id_, embed in batch:
            is_image_file = are_valid_files(self.valid_img_exts, [id_])
            is_text_file = are_valid_files(self.valid_txt_exts, [id_])
            is_video_file = are_valid_files(self.valid_vid_exts, [id_])

            if is_image_file:
                partitions['image'][0].append(id_)
                partitions['image'][1].append(embed)
            elif is_text_file:
                partitions['text'][0].append(id_)
                partitions['text'][1].append(embed)
            elif is_video_file:
                partitions['video'][0].append(id_)
                partitions['video'][1].append(embed)
        
        if len(partitions['image'][0]) > 0:
            self.image_store.add(ids = partitions['image'][0],embeddings=partitions['image'][1])
        if len(partitions['text'][0]) > 0:
            self.text_store.add(ids = partitions['text'][0],embeddings=partitions['text'][1])
        if len(partitions['video'][0]) > 0:
            self.video_store.add(ids = partitions['video'][0],embeddings=partitions['video'][1])

