from fastapi import WebSocket
from pydantic import BaseModel
from typing import Literal
from starlette.websockets import WebSocketState

from chromadb import Collection

from smartscan.processor import ProcessorListener
from smartscan.types import ItemEmbedding

class ActiveMessage(BaseModel):
    type: Literal["active"] = "active"
    
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

class FileIndexerWebSocketListener(ProcessorListener[str, ItemEmbedding]):
    def __init__(
            self, 
            ws: WebSocket,
            store: Collection,
            ):
        self.ws = ws
        self.store = store

    async def on_active(self):
        if self.ws.client_state == WebSocketState.CONNECTED:
            try:
                await self.ws.send_json(ActiveMessage().model_dump())  
            except RuntimeError:
                pass 

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
        ids, embeddings = zip(*((item.item_id, item.embedding) for item in batch))
        self.store.add(ids = ids, embeddings=embeddings)

