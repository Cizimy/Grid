import requests
from PIL import Image
import base64
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
# from grid.config import settings # 後で実装する設定化ログをインポート
# import structlog # 後で実装する構造化ログをインポート

# logger = structlog.get_logger(__name__) # ロガーの初期化

class NovelAIClient:
    # Modify the constructor to accept api_key
    def __init__(self, api_key: str):
        # TODO: Load base URL from settings
        # Corrected base URL based on user feedback
        self._base_url = "https://image.novelai.net"
        self._api_key = api_key # Use the provided API key
        self._session = requests.Session()
        self._session.headers.update({
            # Remove 'Bearer ' prefix based on curl example
            "Authorization": f"{self._api_key}",
            "Content-Type": "application/json"
        })
        # logger.info("NovelAIClient initialized")

    def encode_vibe(self, image_path: str, ie_value: float) -> str:
        if not os.path.exists(image_path):
            # logger.error("Image file not found", image_path=image_path)
            raise FileNotFoundError(f"Image file not found at {image_path}")

        try:
            with Image.open(image_path) as img:
                # Convert image to RGB if necessary (NovelAI might expect specific formats)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save image to a buffer and base64 encode
                import io
                buf = io.BytesIO()
                # Change format to JPEG
                img.save(buf, format='JPEG')
                image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        except Exception as e:
            # logger.error("Failed to read or process image", image_path=image_path, error=e)
            raise RuntimeError(f"Failed to read or process image {image_path}: {e}")

        url = f"{self._base_url}/ai/encode-vibe"
        payload = {
            "image": image_base64,
            "information_extracted": ie_value,
            # "mask": "", # Optional
            # "model": "" # Optional
        }

        try:
            # logger.info("Sending encode-vibe request to NovelAI API", image_path=image_path, ie_value=ie_value)
            response = self._session.post(url, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            # Save the binary response content to a file
            encoded_vibe_data = response.content

            # Determine save path (data/encoded/YYYY/MM/DD/vibe_<uuid>.naiv4vibe)
            now = datetime.now()
            save_dir = os.path.join("data", "encoded", str(now.year), f"{now.month:02d}", f"{now.day:02d}")
            os.makedirs(save_dir, exist_ok=True) # Create directories if they don't exist

            vibe_file_name = f"vibe_{uuid.uuid4()}.naiv4vibe" # Use uuid4 for file name
            save_path = os.path.join(save_dir, vibe_file_name)

            with open(save_path, "wb") as f:
                f.write(encoded_vibe_data)

            # logger.info("Encoded vibe saved successfully", save_path=save_path)
            return save_path

        except requests.exceptions.RequestException as e:
            # logger.error("NovelAI API request failed", url=url, error=e)
            raise RuntimeError(f"NovelAI API request failed: {e}")
        except Exception as e:
            # logger.error("Failed to save encoded vibe data", error=e)
            raise RuntimeError(f"Failed to save encoded vibe data: {e}")

    def generate_image(self, prompt: str, model: str, action: str, parameters: Dict[str, Any]) -> List[Tuple[str, bytes]]:
        """
        Generate one or multiple image(s) using NovelAI API.

        Args:
            prompt: The prompt for image generation.
            model: The image model name (e.g., "nai-diffusion-4-full").
            action: The generation type (e.g., "generate").
            parameters: A dictionary of generation parameters.

        Returns:
            A list of tuples, where each tuple contains the filename and binary data of a generated image.

        Raises:
            RuntimeError: If the API request fails or the response is not a valid zip file.
        """
        url = f"{self._base_url}/ai/generate-image"
        payload = {
            "input": prompt,
            "model": model,
            "action": action,
            "parameters": parameters,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}", # Use Bearer scheme
            "Content-Type": "application/json"
        }

        try:
            # logger.info("Sending generate-image request to NovelAI API", model=model, action=action)
            response = self._session.post(url, json=payload, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            # Check if the response is a zip file
            if 'content-type' not in response.headers or response.headers['content-type'] != 'binary/octet-stream':
                 # logger.error("Unexpected content type in generate-image response", content_type=response.headers.get('content-type'))
                 raise RuntimeError(f"Unexpected content type in generate-image response: {response.headers.get('content-type')}")

            # Extract images from the zip file
            import zipfile
            import io
            generated_images = []
            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    for file_info in zf.infolist():
                        with zf.open(file_info) as f:
                            # file_info.filename contains the original filename in the zip
                            generated_images.append((file_info.filename, f.read()))
                # logger.info("Successfully extracted images from zip response", num_images=len(generated_images))
            except zipfile.BadZipFile:
                # logger.error("Received invalid zip file in generate-image response")
                raise RuntimeError("Received invalid zip file in generate-image response")

            return generated_images

        except requests.exceptions.RequestException as e:
            # logger.error("NovelAI API generate-image request failed", url=url, error=e)
            raise RuntimeError(f"NovelAI API generate-image request failed: {e}")
        except Exception as e:
            # logger.error("An unexpected error occurred during generate-image process", error=e)
            raise RuntimeError(f"An unexpected error occurred during generate-image process: {e}")

    # TODO: Implement generate_image method later # Remove this line