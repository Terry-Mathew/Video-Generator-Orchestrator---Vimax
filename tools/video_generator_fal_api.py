import os
from typing import Any, Dict, List, Optional

import fal_client
from tenacity import retry, stop_after_attempt

from interfaces.video_output import VideoOutput
from utils.retry import after_func


class VideoGeneratorFalAPI:
    """Generate videos using Fal.ai hosted models."""

    def __init__(
        self,
        api_key: str,
        model: str = "fal-ai/minimax-video/image-to-video",
        default_arguments: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not api_key:
            raise ValueError("Fal.ai API key is required.")

        os.environ.setdefault("FAL_KEY", api_key)
        self.model = model
        self.default_arguments = default_arguments or {}

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> VideoOutput:
        arguments: Dict[str, Any] = {"prompt": prompt, **self.default_arguments}
        arguments.update(kwargs)

        if reference_image_paths:
            uploaded_urls = [fal_client.upload_file(path) for path in reference_image_paths]
            if uploaded_urls:
                arguments["image_url"] = uploaded_urls[0]
                if len(uploaded_urls) > 1:
                    arguments.setdefault("image_urls", uploaded_urls)

        response = await fal_client.run_async(self.model, arguments=arguments)

        video_info: Optional[Any] = None
        if isinstance(response, dict):
            if "video" in response:
                video_info = response["video"]
            else:
                videos = response.get("videos") or response.get("generated_videos")
                if videos:
                    video_info = videos[0]

        if not video_info:
            raise ValueError("Fal.ai response did not contain a video.")

        if isinstance(video_info, dict):
            url = video_info.get("url") or video_info.get("video_url")
            content_type = video_info.get("content_type", "video/mp4")
        else:
            url = str(video_info)
            content_type = "video/mp4"

        if not url:
            raise ValueError("Fal.ai video response is missing a URL.")

        ext = content_type.split("/")[-1] if "/" in content_type else "mp4"

        return VideoOutput(fmt="url", ext=ext, data=url)

