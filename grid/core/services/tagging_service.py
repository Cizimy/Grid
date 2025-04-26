import json
from typing import Dict, Any, List

# from grid.config import settings # 後で実装する設定管理からインポート
# import structlog # 後で実装する構造化ログをインポート

from grid.core.db.repository import Neo4jRepository
from grid.core.models.image import GeneratedImage

# logger = structlog.get_logger(__name__) # ロガーの初期化

class TaggingService:
    def __init__(self, neo4j_repo: Neo4jRepository):
        self._neo4j_repo = neo4j_repo
        # logger.info("TaggingService initialized")

    def generate_and_add_tags(self, image: GeneratedImage):
        """
        Generate simple tags based on image parameters and prompt, and add them to the image in the database.
        """
        # logger.info("Generating and adding tags for image", image_id=image.imageID)
        generated_tags = []

        # 1. Parameter Tags
        # Assuming actualParameters is a dictionary (or can be parsed from string)
        actual_params: Dict[str, Any] = image.actualParameters
        if isinstance(actual_params, str):
             try:
                 actual_params = json.loads(actual_params)
             except json.JSONDecodeError:
                 # logger.error("Failed to parse actualParameters JSON for tagging", image_id=image.imageID)
                 actual_params = {} # Use empty dict if parsing fails

        # Example: Add tags for steps, scale, sampler, width, height
        param_keys_to_tag = ["steps", "scale", "sampler", "width", "height"]
        for key in param_keys_to_tag:
            if key in actual_params:
                tag_name = f"param:{key}:{actual_params[key]}"
                generated_tags.append(tag_name)
                # logger.debug("Generated parameter tag", image_id=image.imageID, tag=tag_name)

        # 2. Prompt Keyword Tags (Simple version)
        # Split prompt by comma and strip whitespace
        if image.actualPromptPositive:
            keywords = [k.strip() for k in image.actualPromptPositive.split(',') if k.strip()]
            for keyword in keywords:
                tag_name = f"keyword:{keyword}"
                generated_tags.append(tag_name)
                # logger.debug("Generated positive prompt tag", image_id=image.imageID, tag=tag_name)

        if image.actualPromptNegative:
             negative_keywords = [k.strip() for k in image.actualPromptNegative.split(',') if k.strip()]
             for keyword in negative_keywords:
                 tag_name = f"negative_keyword:{keyword}"
                 generated_tags.append(tag_name)
                 # logger.debug("Generated negative prompt tag", image_id=image.imageID, tag=tag_name)


        # Add generated tags to the database
        for tag_name in generated_tags:
            try:
                self._neo4j_repo.add_tag_to_image(image.imageID, tag_name)
                # logger.debug("Added tag to DB", image_id=image.imageID, tag=tag_name)
            except Exception as e:
                # logger.error("Failed to add tag to DB", image_id=image.imageID, tag_name=tag_name, error=e)
                pass # Continue with other tags

        # logger.info("Finished generating and adding tags for image", image_id=image.imageID, num_tags=len(generated_tags))
        return generated_tags # Return the list of generated tags