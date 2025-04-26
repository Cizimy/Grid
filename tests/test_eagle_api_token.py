import requests
import os
import sys

# Add the parent directory to the sys.path to import modules from grid package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from grid.core.api.eagle import EagleClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the project root (cizimy-grid) or adjust sys.path.")
    sys.exit(1)

def test_api_token():
    eagle_base_url = os.getenv("EAGLE_BASE_URL", "http://localhost:41593") # Keep this for reference, but override below
    eagle_api_token = os.getenv("EAGLE_API_TOKEN")

    if not eagle_api_token:
        print("Error: EAGLE_API_TOKEN environment variable not set.")
        print("Please set it to the token found in Eagle's settings (e.g., http://localhost:41595/?token=YOUR_TOKEN).")
        sys.exit(1)

    print(f"--- Testing Eagle API Token with /api/folder/list ---")
    print(f"Attempting to connect to Eagle API at http://localhost:41595 with token...") # Corrected f-string and port

    try:
        print(f"Debug: Using base URL: http://localhost:41595") # Corrected f-string and indentation, explicit port
        eagle_client = EagleClient(base_url="http://localhost:41595", api_token=eagle_api_token) # Explicitly set base_url to port 41595
        folders = eagle_client.list_folders()
        print("\nSuccessfully retrieved folder list using API token.")
        print(f"Number of folders found: {len(folders)}")
        # Optionally print folder names
        # for folder in folders:
        #     print(f"  - {folder.get('name', 'Unnamed Folder')}")

    except RuntimeError as e:
        print(f"ERROR: Failed to retrieve folder list: {e}")
        print("Please ensure Eagle is running, the API server is enabled, and the EAGLE_BASE_URL and EAGLE_API_TOKEN environment variables are correct.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_api_token()