import neo4j
from typing import Optional, Any, Dict, List
from datetime import datetime
# from grid.config import settings # 後で実装する設定管理からインポート
from grid.core.models.vibe import VibeImage
from grid.core.models.session import GenerationSession # Import GenerationSession
from grid.core.models.image import GeneratedImage # Import GeneratedImage
from grid.core.models.tag import Tag # Import Tag model
# import structlog # 後で実装する構造化ログをインポート

# logger = structlog.get_logger(__name__) # ロガーの初期化

class Neo4jRepository:
    # Modify the constructor to accept connection details
    def __init__(self, uri: str, user: str, password: str):
        self._driver = None
        try:
            self._driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
            # logger.info("Neo4j driver created successfully")
        except Exception as e:
            # logger.error("Failed to create Neo4j driver", error=e)
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")

    def close_connection(self):
        if self._driver:
            self._driver.close()
            # logger.info("Neo4j driver closed")

    def check_connection(self) -> bool:
        if not self._driver:
            return False
        try:
            self._driver.verify_connectivity()
            # logger.info("Neo4j connection verified")
            return True
        except Exception as e:
            # logger.error("Neo4j connection verification failed", error=e)
            return False

    def create_vibe(self, vibe_image: VibeImage):
        def _create_vibe_tx(tx, vibe_data):
            query = """
            CREATE (v:VibeImage {
                vibeID: $vibeID,
                imagePath: $imagePath,
                vibeType: $vibeType,
                encodedIE: $encodedIE,
                encodedVibePath: $encodedVibePath,
                notes: $notes,
                createdAt: $createdAt
            })
            RETURN v
            """
            result = tx.run(query, vibe_data)
            return result.single() is not None # 成功すれば結果が返る

        if not self._driver:
            # logger.error("Driver is not initialized.")
            raise ConnectionError("Database driver is not initialized.")

        vibe_data = vibe_image.model_dump() # Pydanticモデルを辞書に変換
        # Convert datetime to string if necessary, depending on neo4j-driver's handling
        vibe_data['createdAt'] = vibe_data['createdAt'].isoformat() # ISO 8601形式に変換

        try:
            with self._driver.session() as session:
                session.execute_write(_create_vibe_tx, vibe_data)
            # logger.info("Vibe node created successfully", vibe_id=vibe_image.vibeID)
        except Exception as e:
            # logger.error("Failed to create vibe node", vibe_id=vibe_image.vibeID, error=e)
            raise RuntimeError(f"Failed to create vibe node {vibe_image.vibeID}: {e}")

    def get_vibe(self, vibe_id: str) -> Optional[VibeImage]:
        def _get_vibe_tx(tx, vibe_id):
            query = """
            MATCH (v:VibeImage {vibeID: $vibeID})
            RETURN v
            """
            result = tx.run(query, vibeID=vibe_id)
            return result.single()

        if not self._driver:
            # logger.error("Driver is not initialized.")
            raise ConnectionError("Database driver is not initialized.")

        try:
            with self._driver.session() as session:
                record = session.execute_read(_get_vibe_tx, vibe_id)

            if record:
                node = record["v"]
                # Map Neo4j node properties to Pydantic model
                vibe_data = dict(node)
                # Convert datetime string back to datetime object if necessary
                if 'createdAt' in vibe_data and isinstance(vibe_data['createdAt'], str):
                     vibe_data['createdAt'] = datetime.fromisoformat(vibe_data['createdAt'])

                return VibeImage(**vibe_data)
            else:
                # logger.info("Vibe node not found", vibe_id=vibe_id)
                return None
        except Exception as e:
            # logger.error("Failed to get vibe node", vibe_id=vibe_id, error=e)
            raise RuntimeError(f"Failed to get vibe node {vibe_id}: {e}")

    def create_session(self, session: GenerationSession, user_id: str, model_name: str):
        def _create_session_tx(tx, session_data, user_id, model_name):
            # Ensure User node exists (MVP assumes "default" user)
            create_user_query = """
            MERGE (u:User {userID: $userId})
            ON CREATE SET u.createdAt = datetime($createdAt)
            RETURN u
            """
            tx.run(create_user_query, userId=user_id, createdAt=datetime.now().isoformat())

            # Ensure AiModel node exists
            create_model_query = """
            MERGE (m:AiModel {modelName: $modelName})
            ON CREATE SET m.type = 'unknown' // Default type if not specified
            RETURN m
            """
            tx.run(create_model_query, modelName=model_name)

            # Create Session node and relationships
            create_session_query = """
            CREATE (s:GenerationSession {
                sessionID: $sessionID,
                name: $name,
                timestamp: $timestamp,
                baseParameters: $baseParameters,
                basePromptPositive: $basePromptPositive,
                basePromptNegative: $basePromptNegative,
                notes: $notes,
                overallStatus: $overallStatus
            })
            WITH s
            MATCH (u:User {userID: $userId})
            MATCH (m:AiModel {modelName: $modelName})
            CREATE (s)-[:CREATED_BY]->(u)
            CREATE (s)-[:USES_MODEL]->(m)
            RETURN s
            """
            session_data['timestamp'] = session_data['timestamp'].isoformat() # Convert datetime
            tx.run(create_session_query, **session_data, userId=user_id, modelName=model_name)

        if not self._driver:
            raise ConnectionError("Database driver is not initialized.")

        session_data = session.model_dump()

        try:
            # Change session variable name to avoid shadowing
            with self._driver.session() as neo4j_session:
                neo4j_session.execute_write(_create_session_tx, session_data, user_id, model_name)
            # logger.info("Session node created successfully", session_id=session.sessionID)
        except Exception as e:
            # logger.error("Failed to create session node", session_id=session.sessionID, error=e)
            raise RuntimeError(f"Failed to create session node {session.sessionID}: {e}")

    def create_generated_image(self, image: GeneratedImage, session_id: str):
        def _create_image_tx(tx, image_data, session_id):
            # Create GeneratedImage node
            create_image_query = """
            CREATE (i:GeneratedImage {
                imageID: $imageID,
                imagePath: $imagePath,
                seed: $seed,
                actualParameters: $actualParameters,
                actualPromptPositive: $actualPromptPositive,
                actualPromptNegative: $actualPromptNegative,
                rating: $rating,
                eagleItemID: $eagleItemID,
                generationStatus: $generationStatus,
                errorMessage: $errorMessage,
                isVibeCandidate: $isVibeCandidate
            })
            WITH i
            MATCH (s:GenerationSession {sessionID: $sessionId})
            CREATE (i)-[:GENERATED_IN]->(s)
            RETURN i
            """
            # Convert actualParameters dict to string if necessary, depending on neo4j-driver
            # Neo4j driver should handle dicts directly for Map type
            tx.run(create_image_query, **image_data, sessionId=session_id)

        if not self._driver:
            raise ConnectionError("Database driver is not initialized.")

        image_data = image.model_dump()

        try:
            with self._driver.session() as session:
                session.execute_write(_create_image_tx, image_data, session_id)
            # logger.info("GeneratedImage node created successfully", image_id=image.imageID, session_id=session_id)
        except Exception as e:
            # logger.error("Failed to create GeneratedImage node", image_id=image.imageID, session_id=session_id, error=e)
            raise RuntimeError(f"Failed to create GeneratedImage node {image.imageID} for session {session_id}: {e}")

    def update_image_status(self, image_id: str, status: str, error_message: Optional[str] = None):
        def _update_status_tx(tx, image_id, status, error_message):
            update_query = """
            MATCH (i:GeneratedImage {imageID: $imageID})
            SET i.generationStatus = $status,
                i.errorMessage = $errorMessage
            RETURN i
            """
            tx.run(update_query, imageID=image_id, status=status, errorMessage=error_message)

        if not self._driver:
            raise ConnectionError("Database driver is not initialized.")

        try:
            with self._driver.session() as session:
                session.execute_write(_update_status_tx, image_id, status, error_message)
            # logger.info("GeneratedImage status updated", image_id=image_id, status=status)
        except Exception as e:
            # logger.error("Failed to update GeneratedImage status", image_id=image_id, status=status, error=e)
            raise RuntimeError(f"Failed to update status for image {image_id}: {e}")

    def update_image_rating(self, image_id: str, rating: int):
        """
        Update the rating of a GeneratedImage node.
        """
        def _update_rating_tx(tx, image_id, rating):
            update_query = """
            MATCH (i:GeneratedImage {imageID: $imageID})
            SET i.rating = $rating
            RETURN i
            """
            tx.run(update_query, imageID=image_id, rating=rating)

        if not self._driver:
            raise ConnectionError("Database driver is not initialized.")

        if not (0 <= rating <= 5):
            raise ValueError("Rating must be between 0 and 5.")

        try:
            with self._driver.session() as session:
                session.execute_write(_update_rating_tx, image_id, rating)
            # logger.info("GeneratedImage rating updated", image_id=image_id, rating=rating)
        except Exception as e:
            # logger.error("Failed to update GeneratedImage rating", image_id=image_id, rating=rating, error=e)
            raise RuntimeError(f"Failed to update rating for image {image_id}: {e}")

    def add_tag_to_image(self, image_id: str, tag_name: str):
        """
        Add a tag to a GeneratedImage node. Creates the Tag node if it doesn't exist.
        """
        def _add_tag_tx(tx, image_id, tag_name):
            # MERGE creates the Tag node if it doesn't exist
            query = """
            MATCH (i:GeneratedImage {imageID: $imageID})
            MERGE (t:Tag {tagName: $tagName})
            CREATE (i)-[:HAS_TAG]->(t)
            RETURN i, t
            """
            tx.run(query, imageID=image_id, tagName=tag_name)

        if not self._driver:
            raise ConnectionError("Database driver is not initialized.")

        try:
            with self._driver.session() as session:
                session.execute_write(_add_tag_tx, image_id, tag_name)
            # logger.info("Tag added to GeneratedImage", image_id=image_id, tag_name=tag_name)
        except Exception as e:
            # logger.error("Failed to add tag to GeneratedImage", image_id=image_id, tag_name=tag_name, error=e)
            raise RuntimeError(f"Failed to add tag '{tag_name}' to image {image_id}: {e}")

    # TODO: Add methods for other nodes (Session, Image, etc.)