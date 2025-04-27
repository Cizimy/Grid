import json
import os # osモジュールをインポート
from typing import List, Dict, Any, Optional, Tuple

# from grid.config import settings # 後で実装する構造化ログをインポート
# import structlog # 後で実装する構造化ログをインポート

from grid.core.db.repository import Neo4jRepository
from grid.core.api.eagle import EagleClient
from grid.core.services.tagging_service import TaggingService
from grid.core.models.image import GeneratedImage

# logger = structlog.get_logger(__name__) # ロガーの初期化

class EvaluationService:
    def __init__(self, neo4j_repo: Neo4jRepository, eagle_client: EagleClient, tagging_service: TaggingService):
        self._neo4j_repo = neo4j_repo
        self._eagle_client = eagle_client
        self._tagging_service = tagging_service
        # logger.info("EvaluationService initialized")

    def evaluate_and_send_to_eagle(self, image: GeneratedImage, rating: int) -> Tuple[bool, Optional[str]]:
        """
        Sets the rating for a generated image, generates tags, sends it to Eagle,
        updates the database with the Eagle item ID, and updates the rating in Eagle.
        Accepts the GeneratedImage object directly.

        Returns:
            A tuple: (success: bool, error_message: Optional[str]).
            success is True if the process completed without raising an exception, False otherwise.
            error_message contains the error details if success is False.
        """
        # logger.info("Starting evaluation and send to Eagle process for image", image_id=image.imageID, rating=rating)

        try:
            # 1. Update image rating on the object and in DB
            image.rating = rating # Update rating on the object
            self._neo4j_repo.update_image_rating(image.imageID, rating) # Persist rating update
            # logger.debug("Image rating updated in DB", image_id=image.imageID, rating=rating)

            # 2. Generate tags
            # Tagging service adds tags to the DB and returns the list of tag names
            generated_tags = self._tagging_service.generate_and_add_tags(image)
            # logger.debug("Tags generated and added to DB", image_id=image.imageID, tags=generated_tags)

            # 3. Prepare data for Eagle (Add)
            # Use image.imagePath, image.rating, generated_tags, and other image properties for annotation
            # Need to get session ID from the image's relationship. This might require fetching the relationship
            # or ensuring the image object includes session ID. For MVP, let's assume image object has session_id attribute
            # or we can fetch it. Let's add a TODO to refine this.
            # TODO: Ensure GeneratedImage object includes session_id or can easily access it.
            # For now, let's use a placeholder or assume it's available.
            # Let's assume image.sessionID is available for annotation.

            # --- Simplified Annotation Content ---
            annotation_content = f"Image ID: {image.imageID}\n"
            # annotation_content += f"Session ID: {image.sessionID}\n" # TODO: Get actual session ID
            annotation_content += f"Seed: {image.seed}\n"
            annotation_content += f"Prompt: {image.actualPromptPositive}\n"
            if image.actualPromptNegative:
                annotation_content += f"Negative Prompt: {image.actualPromptNegative}\n"
            # Removed detailed parameters from annotation for now
            annotation_content += f"Rating: {image.rating}\n" # Include rating in annotation
            annotation_content += f"Tags: {', '.join(generated_tags)}\n" # Add generated tags to annotation
            # --- End Simplified Annotation Content ---


            # 4. Send to Eagle (Add)
            # add_item_from_paths expects a list of paths, tags, annotation, star
            paths_to_send = [image.imagePath]
            tags_to_send = generated_tags # Send generated tags to Eagle
            annotation_to_send = annotation_content # Send annotation to Eagle
            # star_to_send = image.rating # Star is NOT supported by addFromPaths

            # Use image ID as name for uniqueness in Eagle
            image_name_in_eagle = f"{image.imageID}{os.path.splitext(image.imagePath)[1]}" # Use imageID and original extension

            # logger.info("Sending image to Eagle (Add)", image_id=image.imageID, path=image.imagePath)
            eagle_add_result = self._eagle_client.add_item_from_paths(
                paths=paths_to_send,
                names=[image_name_in_eagle], # Use unique name
                tags=tags_to_send,
                annotation=annotation_to_send
                # star=star_to_send # Star is NOT supported by addFromPaths
            )

            eagle_item_id = None
            # Check if the result is a list and has at least one element
            if isinstance(eagle_add_result, list) and len(eagle_add_result) > 0:
                # Assuming the first element of the list is the item ID string
                eagle_item_id = eagle_add_result[0]
                # logger.info("Image sent to Eagle (Add) successfully", image_id=image.imageID, eagle_item_id=eagle_item_id)
                print(f"DEBUG: Image sent to Eagle (Add) successfully. Eagle Item ID: {eagle_item_id}")

                # 5. Update DB with Eagle item ID
                # TODO: Implement update_image_eagle_id method in Neo4jRepository
                # This method would update the eagleItemID property of the GeneratedImage node.
                # For now, let's add a print statement and a TODO.
                print(f"DEBUG: TODO: Implement update_image_eagle_id in Neo4jRepository and save ID: {eagle_item_id}")
                # self._neo4j_repo.update_image_eagle_id(image.imageID, eagle_item_id) # Placeholder call
                # logger.info("GeneratedImage node update planned with Eagle item ID", image_id=image.imageID, eagle_item_id=eagle_item_id)

                # 6. Update rating in Eagle using the update API
                try:
                    # logger.info("Updating rating in Eagle", eagle_item_id=eagle_item_id, rating=image.rating)
                    self._eagle_client.update_item(item_id=eagle_item_id, star=image.rating)
                    # logger.info("Rating updated in Eagle successfully", eagle_item_id=eagle_item_id, rating=image.rating)
                    print(f"DEBUG: Rating updated in Eagle successfully for item {eagle_item_id} to {image.rating} stars.")
                except Exception as update_e:
                    # logger.error("Failed to update rating in Eagle", eagle_item_id=eagle_item_id, rating=image.rating, error=update_e)
                    print(f"ERROR: Failed to update rating in Eagle for item {eagle_item_id}: {update_e}")
                    # Decide if this failure should cause the whole process to fail
                    # For now, let's log and continue, but return False for the overall process
                    return False, f"Failed to update rating in Eagle for item {eagle_item_id}: {update_e}"


            else:
                # logger.warning("Failed to get Eagle item ID from addFromPaths response", image_id=image.imageID, response=eagle_add_result)
                print(f"WARNING: Failed to get Eagle item ID for image {image.imageID} from addFromPaths response. Response: {eagle_add_result}")
                return False, f"Failed to add image to Eagle or get item ID for image {image.imageID}. Response: {eagle_add_result}"


            # logger.info("Evaluation and send to Eagle process completed for image", image_id=image.imageID)
            return True, None # Success

        except ValueError as e:
            # logger.error("Validation error during evaluation/send to Eagle", image_id=image.imageID, error=e)
            error_msg = f"Validation error for image {image.imageID}: {e}"
            print(f"ERROR: {error_msg}")
            return False, error_msg
        except RuntimeError as e:
            # logger.error("Runtime error during evaluation/send to Eagle", image_id=image.imageID, error=e)
            error_msg = f"Runtime error for image {image.imageID}: {e}"
            print(f"ERROR: {error_msg}")
            return False, error_msg
        except Exception as e:
            # logger.error("An unexpected error occurred during evaluation/send to Eagle", image_id=image.imageID, error=e)
            error_msg = f"An unexpected error occurred for image {image.imageID}: {e}"
            print(f"ERROR: {error_msg}")
            return False, error_msg