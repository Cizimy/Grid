import uuid # Import uuid module
from datetime import datetime
import requests # Import requests
import os # Import os
import base64 # Import base64
from PIL import Image # Import Image
import io # Import io

from typing import Optional
# import structlog # 後で実装する構造化ログをインポート

# from grid.config import settings # 後で実装する設定管理からインポート
from grid.core.db.repository import Neo4jRepository
from grid.core.models.vibe import VibeImage
# from novelai_api.NovelAI_API import NovelAIAPI # novelai-apiは直接encode-vibeを提供しないため使用しない

# logger = structlog.get_logger(__name__) # ロガーの初期化

class LibraryService:
    # Modify constructor to accept Neo4jRepository and potentially settings
    def __init__(self, neo4j_repo: Neo4jRepository):
        self._neo4j_repo = neo4j_repo
        # TODO: Load NovelAI API key and base URL from settings
        self._novelai_api_key = os.getenv("NOVELAI_API_KEY") # Temporarily load from env var
        self._novelai_base_url = "https://image.novelai.net" # Base URL for image API
        # logger.info("LibraryService initialized")

    def _encode_vibe_api_call(self, image_path: str, ie_value: float) -> str:
        """Internal method to call NovelAI /ai/encode-vibe endpoint directly."""
        if not os.path.exists(image_path):
            # logger.error("Image file not found for encoding", image_path=image_path)
            raise FileNotFoundError(f"Image file not found at {image_path}")

        try:
            with Image.open(image_path) as img:
                # Convert image to RGB if necessary (JPEG does not support alpha channel)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Save image to a buffer and base64 encode
                buf = io.BytesIO()
                img.save(buf, format='JPEG') # Use JPEG format
                image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        except Exception as e:
            # logger.error("Failed to read or process image for encoding", image_path=image_path, error=e)
            raise RuntimeError(f"Failed to read or process image {image_path}: {e}")

        url = f"{self._novelai_base_url}/ai/encode-vibe"
        payload = {
            "image": image_base64,
            # Cast ie_value to int
            "information_extracted": int(ie_value),
            # Set model to the specific value from Web UI example
            "model": "nai-diffusion-4-full"
            # Remove mask parameter as it's not in the Web UI example
            # "mask": "", # Add mask parameter with empty string
        }

        headers = {
            "Authorization": f"Bearer {self._novelai_api_key}", # Keep Bearer scheme for now
            "Content-Type": "application/json"
        }

        try:
            # logger.info("Sending encode-vibe request to NovelAI API", image_path=image_path, ie_value=ie_value)
            response = requests.post(url, json=payload, headers=headers)
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
            # logger.error("NovelAI API encode-vibe request failed", url=url, error=e)
            raise RuntimeError(f"NovelAI API encode-vibe request failed: {e}")
        except Exception as e:
            # logger.error("Failed to save encoded vibe data after API call", error=e)
            raise RuntimeError(f"Failed to save encoded vibe data: {e}")


    def register_vibe(self, image_path: str, vibe_type: str, ie_value: float, notes: Optional[str] = None) -> VibeImage:
        # logger.info("Starting vibe registration", image_path=image_path, vibe_type=vibe_type, ie_value=ie_value)
        if not self._novelai_api_key:
             raise ValueError("NovelAI API key is not set.")

        try:
            # 1. Encode vibe by calling the API directly
            encoded_vibe_path = self._encode_vibe_api_call(image_path, ie_value)
            # logger.info("Vibe encoded successfully", encoded_vibe_path=encoded_vibe_path)

            # 2. Create VibeImage Pydantic model instance
            vibe_id = str(uuid.uuid4()) # Generate UUIDv4
            created_at = datetime.now()

            vibe_image_model = VibeImage(
                vibeID=vibe_id,
                imagePath=image_path,
                vibeType=vibe_type,
                encodedIE=ie_value,
                encodedVibePath=encoded_vibe_path,
                notes=notes,
                createdAt=created_at
            )
            # logger.info("VibeImage model created", vibe_id=vibe_id)

            # 3. Save VibeImage node to database using Neo4j repository
            self._neo4j_repo.create_vibe(vibe_image_model)
            # logger.info("Vibe node saved to database", vibe_id=vibe_id)

            # logger.info("Vibe registration completed successfully", vibe_id=vibe_id)
            return vibe_image_model

        except FileNotFoundError as e:
            # logger.error("Image file not found during vibe registration", image_path=image_path, error=e)
            raise e # Re-raise the exception
        except RuntimeError as e:
            # logger.error("Error during NovelAI API call or file saving", image_path=image_path, error=e)
            raise e # Re-raise the exception
        except Exception as e:
            # logger.error("An unexpected error occurred during vibe registration", error=e)
            raise RuntimeError(f"Vibe registration failed: {e}") # Wrap unexpected errors

    # TODO: Add other library-related methods later (get_vibe, list_vibes, etc.)