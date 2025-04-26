import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import json # jsonモジュールをインポート

# import structlog # 後で実装する構造化ログをインポート

from grid.core.api.novelai import NovelAIClient
from grid.core.db.repository import Neo4jRepository
from grid.core.models.session import GenerationSession
from grid.core.models.image import GeneratedImage
from grid.core.models.vibe import VibeImage # Needed to process vibe info from session

# logger = structlog.get_logger(__name__) # ロガーの初期化

class GenerationService:
    def __init__(self, novelai_client: NovelAIClient, neo4j_repo: Neo4jRepository):
        self._novelai_client = novelai_client
        self._neo4j_repo = neo4j_repo
        # logger.info("GenerationService initialized")

    def generate_images(self, session: GenerationSession, user_id: str) -> List[GeneratedImage]:
        # logger.info("Starting image generation process", session_id=session.sessionID, user_id=user_id)
        generated_images = []

        print(f"DEBUG: Type of session: {type(session)}") # Debug print
        print(f"DEBUG: Session content: {session.model_dump_json()}") # Debug print
        print(f"DEBUG: Session ID: {session.sessionID}") # Debug print

        try:
            # 1. Save session information to database
            # TODO: Get model_name from session or config
            model_name = "nai-diffusion-4-full" # Placeholder model name
            self._neo4j_repo.create_session(session, user_id, model_name)
            # logger.info("Session saved to database", session_id=session.sessionID)

            # 2. Prepare parameters for API call
            # TODO: Extract actual parameters, prompt, vibe info from session
            prompt = session.basePromptPositive
            model = model_name # Use the same model name
            action = "generate" # Assuming normal generation

            # Load parameters from session.baseParameters
            try:
                parameters: Dict[str, Any] = json.loads(session.baseParameters)
            except json.JSONDecodeError as e:
                # logger.error("Failed to parse baseParameters JSON", session_id=session.sessionID, error=e)
                raise ValueError(f"Invalid JSON in session.baseParameters for session {session.sessionID}: {e}")

            # TODO: Add vibe parameters if session includes vibe info
            # if session.vibe_info: # Assuming session has vibe_info attribute
            #     parameters["reference_image_multiple"] = [v.encodedVibePath for v in session.vibe_info] # Need Base64 data, not path
            #     parameters["reference_strength_multiple"] = [v.strength for v in session.vibe_info] # Need strength

            # Ensure model is included in parameters (API requirement)
            parameters["model"] = model # Use the determined model name

            # 3. Execute image generation via API client
            # The generate_image method returns a list of (filename, binary_data) tuples
            generated_image_data = self._novelai_client.generate_image(prompt, model, action, parameters)
            # logger.info("Image generation API call completed", session_id=session.sessionID, num_images=len(generated_image_data))

            # 4. Process and save generated images
            for filename, binary_data in generated_image_data:
                image_id = str(uuid.uuid4()) # Generate UUID for the image
                seed = 0 # TODO: Extract seed from parameters or API response metadata if available
                actual_parameters: Dict[str, Any] = {} # TODO: Extract actual parameters used
                actual_prompt_positive = prompt # Use the prompt sent to API
                actual_prompt_negative = "" # TODO: Extract negative prompt if applicable

                # Determine save path (data/generated/YYYY/MM/DD/<session>/<seed>.png)
                now = datetime.now()
                # Use session ID and seed in the path
                save_dir = os.path.join("data", "generated", str(now.year), f"{now.month:02d}", f"{now.day:02d}", session.sessionID)
                os.makedirs(save_dir, exist_ok=True) # Create directories if they don't exist

                # Use seed in the filename
                image_file_name = f"{seed}.png" # Assuming PNG format
                image_path = os.path.join(save_dir, image_file_name)

                try:
                    with open(image_path, "wb") as f:
                        f.write(binary_data)
                    # logger.info("Generated image saved to file", image_id=image_id, image_path=image_path)

                    # Create GeneratedImage model
                    image_model = GeneratedImage(
                        imageID=image_id,
                        imagePath=image_path,
                        seed=seed,
                        actualParameters=actual_parameters,
                        actualPromptPositive=actual_prompt_positive,
                        actualPromptNegative=actual_prompt_negative,
                        rating=0, # Default rating
                        eagleItemID=None, # Not sent to Eagle yet
                        generationStatus="success", # Assuming success for now
                        errorMessage=None,
                        isVibeCandidate=False # Default
                    )
                    generated_images.append(image_model)

                    # Save GeneratedImage node to database
                    self._neo4j_repo.create_generated_image(image_model, session.sessionID)
                    # logger.info("GeneratedImage node saved to database", image_id=image_id)

                except Exception as e:
                    # logger.error("Failed to save generated image or save to DB", image_id=image_id, error=e)
                    # TODO: Update image status in DB to 'error'
                    # self._neo4j_repo.update_image_status(image_id, "error", str(e))
                    pass # Continue processing other images

            # logger.info("Image generation process completed", session_id=session.sessionID, num_successfully_processed=len(generated_images))
            # TODO: Update session status in DB to 'completed' or 'partially_failed'
            # self._neo4j_repo.update_session_status(session.sessionID, "completed")

        except Exception as e:
            # logger.error("An error occurred during image generation process", session_id=session.sessionID, error=e)
            # TODO: Update session status in DB to 'failed'
            # self._neo4j_repo.update_session_status(session.sessionID, "failed", str(e))
            raise RuntimeError(f"Image generation process failed for session {session.sessionID}: {e}") # Re-raise

        return generated_images

    # TODO: Add other generation-related methods later