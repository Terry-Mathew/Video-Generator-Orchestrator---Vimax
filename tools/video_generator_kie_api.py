import os
import time
import asyncio
from typing import List, Optional
import json

import httpx
from interfaces.image_and_video import VideoOutput

class VideoGeneratorKieAPI:
    def __init__(
        self,
        api_key: str,
        model: str = "veo3",
        base_url: str = "https://api.kie.ai/api/v1/veo",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        size: str = "1600x900",
        seed: Optional[int] = None,
        timeout: int = 600,
    ) -> VideoOutput:
        aspect_ratio = "16:9"
        if size == "1024x1024":
            aspect_ratio = "1:1"
        elif size == "1024x576":
            aspect_ratio = "16:9"
        elif size == "576x1024":
            aspect_ratio = "9:16"

        payload = {
            "prompt": prompt,
            "model": self.model,
            "aspectRatio": aspect_ratio,
        }

        if reference_image_paths:
            payload["imageUrls"] = reference_image_paths

        if seed:
            payload["seeds"] = seed

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate", headers=self.headers, json=payload
            )
            response.raise_for_status()
            task_id = response.json()["data"]["taskId"]

            start_time = time.time()
            while time.time() - start_time < timeout:
                response = await client.get(
                    f"{self.base_url}/record-info?taskId={task_id}", headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                if data["data"]["successFlag"] == 1:
                    video_url = json.loads(data["data"]["resultUrls"])[0]
                    break
                elif data["data"]["successFlag"] in [2, 3]:
                    raise Exception(f"Video generation failed: {data['data'].get('errorMessage')}")
                await asyncio.sleep(30)
            else:
                raise Exception("Video generation timed out")

            video_response = await client.get(video_url)
            video_response.raise_for_status()
            return VideoOutput(video_bytes=video_response.content)
