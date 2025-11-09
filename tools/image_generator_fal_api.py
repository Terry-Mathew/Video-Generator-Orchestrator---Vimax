import os
from typing import Any, Dict, List, Optional

import fal_client
from tenacity import retry, stop_after_attempt

from interfaces.image_output import ImageOutput
from utils.retry import after_func


class ImageGeneratorFalAPI:
    """Generate images using Fal.ai hosted models."""

    def __init__(
        self,
        api_key: str,
        model: str = "fal-ai/flux/dev",
        default_arguments: Optional[Dict[str, Any]] = None,
        num_images: int = 1,
    ) -> None:
        if not api_key:
            raise ValueError("Fal.ai API key is required.")

        # fal_client falls back to the FAL_KEY environment variable for auth.
        os.environ.setdefault("FAL_KEY", api_key)
        self.model = model
        self.default_arguments = default_arguments or {}
        self.num_images = num_images

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        aspect_ratio: Optional[str] = None,
        **kwargs: Any,
    ) -> ImageOutput:
        arguments: Dict[str, Any] = {"prompt": prompt, **self.default_arguments}
        if aspect_ratio is not None:
            arguments["aspect_ratio"] = aspect_ratio

        arguments.update(kwargs)

        if reference_image_paths:
            uploaded_urls = [fal_client.upload_file(path) for path in reference_image_paths]
            if len(uploaded_urls) == 1:
                arguments.setdefault("image_url", uploaded_urls[0])
            else:
                arguments.setdefault("image_urls", uploaded_urls)

        if self.num_images:
            arguments.setdefault("num_images", self.num_images)

        response = await fal_client.run_async(self.model, arguments=arguments)
        images = response.get("images") or []
        if not images:
            raise ValueError("Fal.ai response did not contain any images.")

        image_info = images[0]
        url = image_info["url"]
        content_type = image_info.get("content_type", "image/png")
        ext = content_type.split("/")[-1] if "/" in content_type else "png"

        return ImageOutput(fmt="url", ext=ext, data=url)

