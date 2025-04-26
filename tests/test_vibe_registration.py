import os
import sys
import uuid
from datetime import datetime

# Add the parent directory to the sys.path to import modules from grid package
# Assuming the script is run from cizimy-grid directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    # Remove NovelAIClient import
    # from grid.core.api.novelai import NovelAIClient
    from grid.core.db.repository import Neo4jRepository
    from grid.core.services.library_service import LibraryService
    from grid.core.models.vibe import VibeImage
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the project root (cizimy-grid) or adjust sys.path.")
    sys.exit(1)


def main():
    # Load sensitive information from environment variables
    novelai_api_key = os.getenv("NOVELAI_API_KEY")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not novelai_api_key:
        print("Error: NOVELAI_API_KEY environment variable not set.")
        sys.exit(1)
    if not neo4j_password:
        print("Error: NEO4J_PASSWORD environment variable not set.")
        sys.exit(1)

    image_path = r"C:\Users\Kenichi\Documents\Cizimy\ソラ_しゃがみ_フロント_体操服.png"
    vibe_type = "Generic"
    ie_value = 1.0
    notes = "Test vibe registration from CLI"

    # Check if the image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        sys.exit(1)

    # novelai_client = None # Remove novelai_client initialization
    neo4j_repo = None
    try:
        # Initialize clients and repository
        # novelai_client = NovelAIClient(api_key=novelai_api_key) # Remove NovelAIClient initialization
        neo4j_repo = Neo4jRepository(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)

        # Check DB connection
        if not neo4j_repo.check_connection():
             print("Error: Could not connect to Neo4j database. Please ensure it is running.")
             sys.exit(1)
        print("Successfully connected to Neo4j.")

        # Pass only neo4j_repo to LibraryService
        library_service = LibraryService(neo4j_repo)

        print(f"Registering vibe for image: {image_path}")
        registered_vibe = library_service.register_vibe(image_path, vibe_type, ie_value, notes)

        print("\nVibe Registration Successful:")
        print(f"  Vibe ID: {registered_vibe.vibeID}")
        print(f"  Original Image Path: {registered_vibe.imagePath}")
        print(f"  Encoded Vibe Path: {registered_vibe.encodedVibePath}")
        print(f"  Vibe Type: {registered_vibe.vibeType}")
        print(f"  IE Value: {registered_vibe.encodedIE}")
        print(f"  Notes: {registered_vibe.notes}")
        print(f"  Created At: {registered_vibe.createdAt}")

        # Optional: Verify in DB
        print(f"\nVerifying vibe with ID {registered_vibe.vibeID} in database...")
        retrieved_vibe = neo4j_repo.get_vibe(registered_vibe.vibeID)

        if retrieved_vibe:
            print("Successfully retrieved vibe from DB:")
            print(f"  Vibe ID: {retrieved_vibe.vibeID}")
            # Add more checks if needed
        else:
            print(f"Error: Vibe with ID {registered_vibe.vibeID} not found in DB.")

        # Optional: Verify encoded file exists
        print(f"\nVerifying encoded vibe file exists at {registered_vibe.encodedVibePath}...")
        if os.path.exists(registered_vibe.encodedVibePath):
            print("Encoded vibe file found.")
        else:
            print("Error: Encoded vibe file not found.")


    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except RuntimeError as e:
        print(f"Runtime error during process: {e}")
    except ConnectionError as e:
        print(f"Database connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if neo4j_repo:
            neo4j_repo.close_connection()
            print("\nNeo4j connection closed.")


if __name__ == "__main__":
    main()