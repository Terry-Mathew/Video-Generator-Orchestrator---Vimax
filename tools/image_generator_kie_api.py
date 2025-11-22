import base64
import os
import random
import time
import asyncio
from typing import List, Optional

import httpx
from PIL import Image

from interfaces.image_and_video import ImageOutput


class ImageGeneratorKieAPI:
    def __init__(
        self,
        api_key: str,
        model: str = "flux-kontext-pro",
        base_url: str = "https://api.kie.ai/api/v1/flux/kontext",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        size: str = "1600x900",
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        timeout: int = 300,
    ) -> ImageOutput:
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
            "aspectRatio": aspect_ratio
        }

        if reference_image_paths:
            payload["inputImage"] = reference_image_paths[0]

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
                data = response.json()["data"]
                if data["successFlag"] == 1:
                    image_url = data["response"]["resultImageUrl"]
                    break
                elif data["successFlag"] in [2, 3]:
                    raise Exception(f"Image generation failed: {data.get('errorMessage')}")
                await asyncio.sleep(3)
            else:
                raise Exception("Image generation timed out")

            image_response = await client.get(image_url)
            image_response.raise_for_status()
            return ImageOutput(image_bytes=image_response.content)
