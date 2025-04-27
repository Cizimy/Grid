import os
import sys
import uuid
from datetime import datetime
import json
import time # Add time module for potential delays
from PIL import Image # Import Image from Pillow

# Add the parent directory to the sys.path to import modules from grid package
# Assuming the script is run from cizimy-grid directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# DEBUG: Print current working directory
print(f"DEBUG: Current working directory: {os.getcwd()}")

try:
    from grid.core.api.novelai import NovelAIClient
    from grid.core.api.eagle import EagleClient # Import EagleClient
    from grid.core.db.repository import Neo4jRepository
    from grid.core.services.generation_service import GenerationService
    from grid.core.services.tagging_service import TaggingService # Import TaggingService
    from grid.core.services.evaluation_service import EvaluationService # Import EvaluationService
    from grid.core.models.session import GenerationSession
    from grid.core.models.image import GeneratedImage
    from grid.core.models.user import User # Import User model if needed for user creation
    from grid.core.models.ai_model import AiModel # Import AiModel model if needed for model creation
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the project root (cizimy-grid) or adjust sys.path.")
    sys.exit(1)

def main():
    # Load sensitive information from environment variables
    novelai_api_key = os.getenv("NOVELAI_API_KEY")
    # Correct the default Neo4j URI port to 7474 based on Docker port mapping
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7474")
    neo4j_user = os.getenv("NEO4j_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    # Eagle base URL and Token
    # Correct the default port to 41595 based on user provided info
    eagle_base_url = os.getenv("EAGLE_BASE_URL", "http://localhost:41595") # Keep this for reference, but override below
    eagle_api_token = os.getenv("EAGLE_API_TOKEN") # Load Eagle API token from environment variable


    if not novelai_api_key:
        print("Error: NOVELAI_API_KEY environment variable not set.")
        sys.exit(1)
    if not neo4j_password:
        print("Error: NEO4J_PASSWORD environment variable not set.")
        sys.exit(1)
    # Eagle API token is now required for the test
    if not eagle_api_token:
        print("Error: EAGLE_API_TOKEN environment variable not set.")
        print("Please set it to the token found in Eagle's settings (e.g., http://localhost:41595/?token=YOUR_TOKEN).")
        sys.exit(1)


    # --- Test Eagle API Connection (get_application_info and list_folders) ---
    print("--- Testing Eagle API Connection (get_application_info and list_folders) ---")
    eagle_client = None
    try:
        # Explicitly set base_url to port 41595 based on successful access info
        eagle_client = EagleClient(base_url="http://localhost:41595", api_token=eagle_api_token)
        print(f"Attempting to connect to Eagle API at http://localhost:41595...")

        # Test get_application_info (does not require token)
        app_info = eagle_client.get_application_info()
        print("\nSuccessfully connected to Eagle API and retrieved application info.")
        print(f"Eagle Version: {app_info.get('version')}")
        print(f"Eagle Platform: {app_info.get('platform')}")

        # Test list_folders (requires token)
        print("\nAttempting to retrieve folder list (requires token)...")
        folders = eagle_client.list_folders()
        print("\nSuccessfully retrieved folder list using API token.")
        print(f"Number of folders found: {len(folders)}")
        # Optionally print folder names
        # for folder in folders:
        #     print(f"  - {folder.get('name', 'Unnamed Folder')}")


    except RuntimeError as e:
        print(f"ERROR: Failed to connect to Eagle API or retrieve data: {e}")
        print("Please ensure Eagle is running, the API server is enabled, and the EAGLE_BASE_URL and EAGLE_API_TOKEN environment variables are correct.")
        # Exit if Eagle connection fails, as subsequent tests will also fail
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during Eagle API connection test: {e}")
        sys.exit(1)


    # --- Test GenerationService ---
    print("\n--- Testing GenerationService ---")

    novelai_client = None
    neo4j_repo = None
    all_generated_images = [] # Use a new list to collect all generated images
    try:
        # Initialize clients and repository
        novelai_client = NovelAIClient(api_key=novelai_api_key)
        # Use the potentially updated neo4j_uri with correct port
        neo4j_repo = Neo4jRepository(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
        # EagleClient is already initialized above

        # Check DB connection
        if not neo4j_repo.check_connection():
             print("Error: Could not connect to Neo4j database. Please ensure it is running.")
             sys.exit(1)
        print("Successfully connected to Neo4j.")


        generation_service = GenerationService(novelai_client, neo4j_repo)
        tagging_service = TaggingService(neo4j_repo) # Initialize TaggingService
        evaluation_service = EvaluationService(neo4j_repo, eagle_client, tagging_service) # Initialize EvaluationService


        # Create a test GenerationSession object
        test_session_id = str(uuid.uuid4())
        test_user_id = "default" # Using the default user for MVP

        # Define test parameters based on WebUI payload example
        parameters_dict = {
            "params_version": 3,
            "width": 512,
            "height": 512,
            "scale": 7,
            "sampler": "k_euler_ancestral",
            "steps": 28,
            "n_samples": 1, # Generate 1 image per request
            "seed": int(time.time()), # Use current timestamp as base seed
            "ucPreset": 0,
            "qualityToggle": False,
            "autoSmea": False,
            "dynamic_thresholding": False,
            "controlnet_strength": 1,
            "legacy": False,
            "add_original_image": True,
            "cfg_rescale": 0.06,
            "noise_schedule": "karras",
            "legacy_v3_extend": False,
            "skip_cfg_above_sigma": 19.34,
            "use_coords": False,
            "legacy_uc": False,
            "v4_prompt": {"caption": {"base_caption": "1girl, solo, white background", "char_captions": []}, "use_coords": False, "use_order": True},
            "v4_negative_prompt": {"caption": {"base_caption": "blurry, lowres, worst quality, bad quality", "char_captions": []}, "legacy_uc": False},
            "normalize_reference_strength_multiple": False,
            "characterPrompts": [],
            "negative_prompt": "blurry, lowres, worst quality, bad quality",
            "deliberate_euler_ancestral_bug": False,
            "prefer_brownian": True
        }
        test_base_parameters_json = json.dumps(parameters_dict)
        test_prompt_positive = "1girl, solo, white background"
        test_prompt_negative = "blurry, lowres, worst quality, bad quality"

        test_session = GenerationSession(
            sessionID=test_session_id,
            name="Test Generation Session",
            timestamp=datetime.now(),
            baseParameters=test_base_parameters_json,
            basePromptPositive=test_prompt_positive,
            basePromptNegative=test_prompt_negative,
            notes="CLI test session",
            overallStatus="pending"
        )

        print(f"\nStarting image generation for session: {test_session_id}")

        num_images_to_generate = 3 # Generate 3 images as per user instruction

        for i in range(num_images_to_generate):
            print(f"\nGenerating image {i + 1}/{num_images_to_generate} for session: {test_session_id}")
            # Update seed for each generation
            parameters_dict["seed"] = int(time.time()) + i # Ensure unique seed for each generation
            test_base_parameters_json = json.dumps(parameters_dict)
            test_session.baseParameters = test_base_parameters_json # Update session object with new parameters

            # Generate a single image
            generated_image_list = generation_service.generate_images(test_session, test_user_id)
            if generated_image_list:
                all_generated_images.extend(generated_image_list)
                print(f"Generated image ID: {generated_image_list[0].imageID}")
            else:
                print(f"Error: Image generation failed for image {i + 1}.")
                # Depending on requirements, might want to exit or handle this failure

            time.sleep(1) # Add a small delay between generations to ensure unique timestamps for seeds

        print("\nImage Generation Process Completed.")
        print(f"Total number of images processed: {len(all_generated_images)}")

        # Verify generation results (optional, can be removed for final test script)
        print("\nVerifying generated images and DB records...")
        for image in all_generated_images:
            print(f"  Verifying image ID: {image.imageID}")
            print(f"    Image Path: {image.imagePath}")
            print(f"    Seed: {image.seed}")
            print(f"    Status: {image.generationStatus}")
            print(f"    Verify DB record for image {image.imageID} and session {test_session_id} manually in Neo4j Browser.")

        print("\nGenerationService test finished.")

        # --- Test EvaluationService and Eagle Integration (Full) ---
        print("\n--- Testing EvaluationService and Eagle Integration (Full) ---")

        if len(all_generated_images) >= 1:
            # Use the first generated image for Full test
            image_to_evaluate_full = all_generated_images[0]
            test_rating_full = 5 # Set a test rating

            print(f"\nEvaluating image {image_to_evaluate_full.imageID} with rating {test_rating_full} and sending to Eagle (Full process)...")

            # Call the evaluation service and check the result tuple
            success_full, error_message_full = evaluation_service.evaluate_and_send_to_eagle(image_to_evaluate_full, test_rating_full)

            if success_full:
                print("\nEvaluation and Eagle send (Full process) completed SUCCESSFULLY.")
                print(f"Please verify in Eagle that the image '{os.path.basename(image_to_evaluate_full.imagePath)}' was added with:")
                print(f"  - Rating: {test_rating_full} stars")
                print(f"  - Tags: Parameter tags (e.g., param:steps:28) and prompt keyword tags (e.g., keyword:1girl)")
                print(f"  - Annotation: Contains details like Image ID, Seed, Prompt, Parameters, Rating, and Tags.")
                print(f"\nManual verification in Eagle is required to confirm success for the FULL process.")
            else:
                print(f"\nEvaluation and Eagle send (Full process) FAILED: {error_message_full}")
                print("Proceeding to Minimal Eagle Integration tests.")

        else:
            print("\nSkipping Full EvaluationService and Eagle test as not enough images were generated.")

        # --- Test Eagle Integration (Minimal - addFromPaths) ---
        print("\n--- Testing Eagle Integration (Minimal - addFromPaths) ---")

        if len(all_generated_images) >= 2:
            # Use the second generated image for Minimal addFromPaths test
            image_to_evaluate_minimal_paths = all_generated_images[1]

            print(f"\nAttempting to add item to Eagle with minimal data (addFromPaths): {image_to_evaluate_minimal_paths.imagePath}")

            try:
                # Call EagleClient directly with minimal data using addFromPaths
                minimal_eagle_result_paths = eagle_client.add_item_from_paths(
                    paths=[image_to_evaluate_minimal_paths.imagePath],
                    names=[os.path.basename(image_to_evaluate_minimal_paths.imagePath)] # Add name
                )

                print("\nMinimal Eagle send (addFromPaths) process completed.")
                if minimal_eagle_result_paths and len(minimal_eagle_result_paths) > 0 and "id" in minimal_eagle_result_paths[0]:
                     print(f"Successfully added item to Eagle with minimal data (addFromPaths). Eagle Item ID: {minimal_eagle_result_paths[0]['id']}")
                     print(f"Please verify in Eagle that the image '{os.path.basename(image_to_evaluate_minimal_paths.imagePath)}' was added with NO tags, NO annotation, and 0 stars.")
                else:
                     print(f"Warning: Minimal Eagle send (addFromPaths) process did not return an item ID. Response: {minimal_eagle_result_paths}")

            except RuntimeError as e:
                print(f"ERROR: Runtime error during minimal Eagle send (addFromPaths) process: {e}")
            except Exception as e:
                print(f"ERROR: An unexpected error occurred during minimal Eagle send (addFromPaths) process: {e}")

        else:
             print("\nSkipping Minimal addFromPaths test as not enough images were generated.")


        # --- Test Eagle Integration (Minimal - addFromPath) ---
        print("\n--- Testing Eagle Integration (Minimal - addFromPath) ---")

        if len(all_generated_images) >= 3:
            # Use the third generated image for Minimal addFromPath test
            image_to_evaluate_minimal_path = all_generated_images[2]

            print(f"\nAttempting to add item to Eagle with minimal data (addFromPath): {image_to_evaluate_minimal_path.imagePath}")

            try:
                # Call EagleClient directly with minimal data using addFromPath
                minimal_eagle_result_path = eagle_client.add_item_from_path(
                    path=image_to_evaluate_minimal_path.imagePath,
                    name=os.path.basename(image_to_evaluate_minimal_path.imagePath) # Add name
                )

                print("\nMinimal Eagle send (addFromPath) process completed.")
                if minimal_eagle_result_path and "id" in minimal_eagle_result_path:
                     print(f"Successfully added item to Eagle with minimal data (addFromPath). Eagle Item ID: {minimal_eagle_result_path['id']}")
                     print(f"Please verify in Eagle that the image '{os.path.basename(image_to_evaluate_minimal_path.imagePath)}' was added with NO tags, NO annotation, and 0 stars.")
                else:
                     print(f"Warning: Minimal Eagle send (addFromPath) process did not return item data. Response: {minimal_eagle_result_path}")

            except RuntimeError as e:
                print(f"ERROR: Runtime error during minimal Eagle send (addFromPath) process: {e}")
            except Exception as e:
                print(f"ERROR: An unexpected error occurred during minimal Eagle send (addFromPath) process: {e}")

        else:
             print("\nSkipping Minimal addFromPath test as not enough images were generated.")

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
        # No explicit close needed for requests.Session

if __name__ == "__main__":
    main()