import numpy as np
from fastapi import WebSocket
from chromadb import Collection
from smartscan.utils import are_valid_files
from smartscan.processor import ProcessorListener


class FileIndexerWebSocketListener(ProcessorListener[str, tuple[str, np.ndarray]]):
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
        await self.ws.send_json({
            "type": "progress",
            "progress": progress
        })        
    
    async def on_fail(self, result):
        await self.ws.send_json({
            "type": "fail",
            "error": str(result.error)
        })

    async def on_error(self, e, item):
        await self.ws.send_json({
            "type": "error",
            "error": str(e),
            "item": item
        })

    async def on_complete(self, result):
        await self.ws.send_json({
            "type": "complete",
            "total_processed": result.total_processed,
            "time_elapsed": result.time_elapsed
        })

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

