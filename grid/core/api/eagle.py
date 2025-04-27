import requests
import json
import os
from typing import List, Dict, Any, Optional, Tuple # Tupleを追加

# from grid.config import settings # 後で実装する設定管理からインポート
# import structlog # 後で実装する構造化ログをインポート

# logger = structlog.get_logger(__name__) # ロガーの初期化

class EagleClient:
    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None):
        # 環境変数から設定を読み込む。環境変数が設定されていない場合は引数の値（またはデフォルト値）を使用。
        self._base_url = os.environ.get("EAGLE_BASE_URL", base_url if base_url is not None else "http://localhost:41595")
        self._api_token = os.environ.get("EAGLE_API_TOKEN", api_token) # Store the API token

        self._session = requests.Session()
        # Eagle API v4.0 does not require Authorization header for addFromPaths
        # self._session.headers.update({
        #     "Authorization": f"Bearer {api_key}", # If API key is needed for other endpoints
        #     "Content-Type": "application/json" # addFromPaths uses multipart/form-data implicitly
        # })
        # logger.info("EagleClient initialized", base_url=self._base_url)

    def add_item_from_paths(self, paths: List[str], names: Optional[List[str]] = None, tags: Optional[List[str]] = None, annotation: Optional[str] = None, star: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Adds multiple items to Eagle from local file paths using the addFromPaths API (v4.0+).

        Args:
            paths: A list of absolute paths to the image files.
            names: A list of names for the items. Must be the same length as paths.
            tags: A list of tags to apply to all added items.
            annotation: A note/description to add to all items.
            star: A star rating (0-5) to apply to all items.

        Returns:
            A list of dictionaries, each representing the result for an added item,
            including the eagleItemID.

        Raises:
            RuntimeError: If the API request fails or returns an unexpected response.
            ValueError: If names list is provided but its length does not match paths.
        """
        url = f"{self._base_url}/api/item/addFromPaths"
        # logger.info("Sending addFromPaths request to Eagle API", num_paths=len(paths))

        if names is not None and len(names) != len(paths):
             raise ValueError("Length of names list must match length of paths list.")

        # Add token as a query parameter if available
        params = {}
        if self._api_token:
            params["token"] = self._api_token

        # Normalize paths to use forward slashes and convert to absolute paths
        processed_paths = []
        for path in paths:
             absolute_path = os.path.abspath(path) # Convert to absolute path
             normalized_path = absolute_path.replace(os.sep, '/') # Normalize to forward slashes
             processed_paths.append(normalized_path)

        # logger.debug("Processed paths for Eagle API", original_paths=paths, processed_paths=processed_paths)

        # Construct the JSON body based on API documentation
        items_payload = []
        for i, path in enumerate(processed_paths):
            item_data: Dict[str, Any] = {
                "path": path # Use processed (absolute and normalized) path
            }
            # Always add name, using provided name if available, otherwise extract from path
            if names is not None and i < len(names):
                item_data["name"] = names[i]
            else:
                item_data["name"] = os.path.basename(path) # Extract name from path if not provided

            # Add tags and annotation to EACH item in the items list
            if tags is not None:
                item_data["tags"] = tags
            if annotation is not None:
                item_data["annotation"] = annotation
            # Note: star is NOT supported by addFromPaths according to documentation/testing
            # If star is needed, it must be set via the update API after adding the item.
            # if star is not None:
            #     if not (0 <= star <= 5):
            #          raise ValueError("Star rating must be between 0 and 5.")
            #     item_data["star"] = star # Add star to each item if supported

            items_payload.append(item_data)

        payload: Dict[str, Any] = {
            "items": items_payload
        }

        # Note: Batch-level parameters like folderId would go here if needed
        # if folder_id is not None:
        #     payload["folderId"] = folder_id


        headers = {
            "Content-Type": "application/json" # Explicitly set Content-Type to application/json
        }


        try:
            print(f"DEBUG: Sending addFromPaths payload: {json.dumps(payload, indent=2)}") # Add debug print for payload
            # Use json parameter for JSON body and params for query parameters
            response = self._session.post(url, json=payload, params=params, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            result = response.json()

            # Check for "success" status in the response
            if result.get("status") != "success":
                 # logger.error("Eagle API returned error status", status=result.get("status"), message=result.get("message"))
                 raise RuntimeError(f"Eagle API returned error: {result.get('message', 'Unknown error')}")

            # The 'data' field in the response contains the list of added items with their IDs
            added_items = result.get("data", [])
            # logger.info("Successfully added items to Eagle", num_added=len(added_items))
            return added_items

        except requests.exceptions.RequestException as e:
            # logger.error("Eagle API addFromPaths request failed", url=url, error=e)
            raise RuntimeError(f"Eagle API request failed: {e}")
        except json.JSONDecodeError:
            # logger.error("Failed to parse Eagle API response JSON")
            raise RuntimeError("Failed to parse Eagle API response JSON")
        except Exception as e:
            # logger.error("An unexpected error occurred during Eagle API call", error=e)
            raise RuntimeError(f"An unexpected error occurred during Eagle API call: {e}")

    def add_item_from_path(self, path: str, name: str, tags: Optional[List[str]] = None, annotation: Optional[str] = None, star: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Adds a single item to Eagle from a local file path using the addFromPath API (v4.0+).

        Args:
            path: The absolute path to the image file.
            name: The name of the item.
            tags: A list of tags to apply to the item.
            annotation: A note/description to add to the item.
            star: A star rating (0-5) to apply to the item.

        Returns:
            A dictionary representing the result for the added item, including the eagleItemID,
            or None if the operation failed.

        Raises:
            RuntimeError: If the API request fails or returns an unexpected response.
        """
        url = f"{self._base_url}/api/item/addFromPath"
        # logger.info("Sending addFromPath request to Eagle API", path=path)

        # Add token as a query parameter if available
        params = {}
        if self._api_token:
            params["token"] = self._api_token

        # Convert to absolute path and normalize to use forward slashes
        absolute_path = os.path.abspath(path) # Convert to absolute path
        processed_path = absolute_path.replace(os.sep, '/') # Normalize to forward slashes

        # logger.debug("Processed path for Eagle API", original_path=path, processed_path=processed_path)

        # Construct the JSON body based on API documentation
        payload: Dict[str, Any] = {
            "path": processed_path, # Use processed (absolute and normalized) path in JSON body
            "name": name # Add required name parameter
        }
        if tags is not None:
            payload["tags"] = tags # Send list directly in JSON body
        if annotation is not None:
            payload["annotation"] = annotation
        # Note: star is NOT supported by addFromPath according to documentation
        # if star is not None:
        #     if not (0 <= star <= 5):
        #          # logger.error("Invalid star rating", star=star)
        #          raise ValueError("Star rating must be between 0 and 5.")
        #     payload["star"] = star # Send integer directly in JSON body

        headers = {
            "Content-Type": "application/json" # Explicitly set Content-Type to application/json
        }

        try:
            print(f"DEBUG: Sending addFromPath payload: {json.dumps(payload, indent=2)}") # Add debug print for payload
            # Use json parameter for JSON body and params for query parameters
            response = self._session.post(url, json=payload, params=params, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            result = response.json()

            # Check for "success" status in the response
            if result.get("status") != "success":
                 # logger.error("Eagle API returned error status for addFromPath", status=result.get("status"), message=result.get("message"))
                 raise RuntimeError(f"Eagle API returned error for addFromPath: {result.get('message', 'Unknown error')}")

            # The 'data' field in the response contains the added item with its ID
            added_item = result.get("data")
            if added_item:
                 # logger.info("Successfully added item to Eagle", eagle_item_id=added_item.get('id'))
                 pass # Log success
            else:
                 # logger.warning("addFromPath did not return item data", response=result)
                 pass # Log warning

            return added_item

        except requests.exceptions.RequestException as e:
            # logger.error("Eagle API addFromPath request failed", url=url, error=e)
            raise RuntimeError(f"Eagle API addFromPath request failed: {e}")
        except json.JSONDecodeError:
            # logger.error("Failed to parse Eagle API addFromPath response JSON")
            raise RuntimeError("Failed to parse Eagle API addFromPath response JSON")
        except Exception as e:
            # logger.error("An unexpected error occurred during addFromPath process", error=e)
            raise RuntimeError(f"An unexpected error occurred during addFromPath process: {e}")


    def update_item(self, item_id: str, tags: Optional[List[str]] = None, annotation: Optional[str] = None, url: Optional[str] = None, star: Optional[int] = None) -> Dict[str, Any]:
        """
        Modifies data of specified fields of an item using the /api/item/update API.

        Args:
            item_id: The ID of the item to be modified.
            tags: Optional list of tags to update.
            annotation: Optional annotation string to update.
            url: Optional source URL to update.
            star: Optional star rating (0-5) to update.

        Returns:
            A dictionary containing the updated item data.

        Raises:
            RuntimeError: If the API request fails or returns an unexpected response.
            ValueError: If item_id is not provided or star rating is invalid.
        """
        if not item_id:
            raise ValueError("item_id is required for updating an item.")

        api_endpoint_url = f"{self._base_url}/api/item/update" # ローカル変数名を変更
        # logger.info("Sending update_item request to Eagle API", item_id=item_id)

        # Add token as a query parameter if available
        params = {}
        if self._api_token:
            params["token"] = self._api_token

        payload: Dict[str, Any] = {
            "id": item_id
        }

        if tags is not None:
            payload["tags"] = tags
        if annotation is not None:
            payload["annotation"] = annotation
        # Ensure 'url' is only added if the 'url' argument is explicitly provided and is not None
        # 修正: 引数として渡されたurlがNoneでないかのみをチェック
        if url is not None:
             payload["url"] = url
        if star is not None:
            if not (0 <= star <= 5):
                 raise ValueError("Star rating must be between 0 and 5.")
            payload["star"] = star

        headers = {
            "Content-Type": "application/json"
        }

        try:
            print(f"DEBUG: Sending update_item payload: {json.dumps(payload, indent=2)}") # Add debug print for payload
            # 修正: リクエスト送信にローカル変数api_endpoint_urlを使用
            response = self._session.post(api_endpoint_url, json=payload, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("status") != "success":
                 raise RuntimeError(f"Eagle API returned error for update_item: {result.get('message', 'Unknown error')}")

            updated_item_data = result.get("data", {})
            # logger.info("Successfully updated item in Eagle", item_id=item_id)
            return updated_item_data

        except requests.exceptions.RequestException as e:
            # logger.error("Eagle API update_item request failed", url=api_endpoint_url, item_id=item_id, error=e) # ログ出力も修正
            raise RuntimeError(f"Eagle API update_item request failed: {e}")
        except json.JSONDecodeError:
            # logger.error("Failed to parse Eagle API update_item response JSON", item_id=item_id)
            raise RuntimeError("Failed to parse Eagle API update_item response JSON")
        except Exception as e:
            # logger.error("An unexpected error occurred during update_item process", item_id=item_id, error=e)
            raise RuntimeError(f"An unexpected error occurred during update_item process: {e}")


    def list_folders(self) -> List[Dict[str, Any]]:
        """
        Lists all folders in the Eagle library using the /api/folder/list API.
        Trying token as query parameter and adding debug output.
        """
        url = f"{self._base_url}/api/folder/list"
        # logger.info("Sending list-folders request to Eagle API (using query param token)")

        params = {}
        if self._api_token:
            params["token"] = self._api_token # トークンをクエリパラメータとして設定
        else:
            # logger.warning("API Token not provided for list_folders")
            print("WARNING: Eagle API Token not provided for list_folders") # トークンがない場合に警告

        headers = {} # ヘッダーからはAuthorizationを削除

        try:
            print(f"DEBUG: Sending GET request to: {url} with params: {params}") # リクエスト情報を出力
            response = self._session.get(url, params=params, headers=headers)

            # --- 詳細なレスポンス情報を取得 ---
            status_code = response.status_code
            response_text = response.text
            # logger.debug("Eagle API list-folders raw response", status_code=status_code, response_text=response_text)
            print(f"DEBUG: list_folders - Status Code: {status_code}") # ステータスコードを出力
            try:
                # JSONとして整形して表示試行
                print(f"DEBUG: list_folders - Response Body (JSON attempt):\n{json.dumps(response.json(), indent=2)}")
            except json.JSONDecodeError:
                # JSONでなければそのまま表示
                print(f"DEBUG: list_folders - Response Body (Raw):\n{response_text}")
            # --- ここまで ---

            # ステータスコードが 200番台でなければここで例外発生
            response.raise_for_status()

            result = response.json()

            # APIレスポンスの形式に合わせて 'status' をチェック (ドキュメントと get_application_info に合わせる)
            response_status = result.get("status")
            if response_status != "success":
                # logger.error("Eagle API returned error status for list-folders", status=response_status, message=result.get("message"))
                raise RuntimeError(f"Eagle API returned error for list-folders: status='{response_status}', message='{result.get('message', 'Unknown error')}'")
            folders = result.get("data", [])
            # logger.info("Successfully retrieved folder list from Eagle", num_folders=len(folders))
            return folders

        # --- エラーハンドリングを強化 ---
        except requests.exceptions.HTTPError as e: # 4xx, 5xx エラー
            # logger.error("Eagle API list-folders HTTP error", url=url, status_code=e.response.status_code, response_text=e.response.text, error=e)
            # エラーレスポンスの内容も含めて例外メッセージを生成
            raise RuntimeError(f"Eagle API list-folders HTTP error: Status={e.response.status_code}, Response='{e.response.text}'") from e
        except requests.exceptions.ConnectionError as e: # 接続エラー
            # logger.error("Eagle API list-folders connection error", url=url, error=e)
            raise RuntimeError(f"Could not connect to Eagle API at {url}. Is Eagle running and API enabled? Error: {e}") from e
        except requests.exceptions.Timeout as e: # タイムアウト
            # logger.error("Eagle API list-folders timeout", url=url, error=e)
            raise RuntimeError(f"Eagle API request timed out for {url}. Error: {e}") from e
        except requests.exceptions.RequestException as e: # その他の requests エラー
            # logger.error("Eagle API list-folders request failed", url=url, error=e)
            raise RuntimeError(f"Eagle API list-folders request failed: {e}") from e
        except json.JSONDecodeError:
            # logger.error("Failed to parse Eagle API list-folders response JSON", response_text=response_text)
            raise RuntimeError(f"Failed to parse Eagle API list-folders response JSON. Raw response: {response_text}")
        except Exception as e:
            # logger.error("An unexpected error occurred during list-folders process", error=e)
            raise RuntimeError(f"An unexpected error occurred during list-folders process: {e}") from e

    def get_application_info(self) -> Dict[str, Any]:
        """
        Gets detailed information on the Eagle App currently running using the /api/application/info API.
        """
        url = f"{self._base_url}/api/application/info"
        # logger.info("Sending get-application-info request to Eagle API")

        # This endpoint does not require a token according to the documentation
        params = {}
        # if self._api_token: # Send token as query parameter if available
        #      params["token"] = self._api_token

        try:
            response = self._session.get(url, params=params)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            result = response.json()

            if result.get("status") != "success": # Note: This endpoint uses "status" instead of "code"
                 # logger.error("Eagle API returned error status for get-application-info", status=result.get("status"), message=result.get("message"))
                 raise RuntimeError(f"Eagle API returned error for get-application-info: {result.get('message', 'Unknown error')}")

            # The 'data' field in the response contains the application info
            app_info = result.get("data", {})
            # logger.info("Successfully retrieved application info from Eagle", version=app_info.get('version'))
            return app_info

        except requests.exceptions.RequestException as e:
            # logger.error("Eagle API get-application-info request failed", url=url, error=e)
            raise RuntimeError(f"Eagle API get-application-info request failed: {e}")
        except json.JSONDecodeError:
            # logger.error("Failed to parse Eagle API get-application-info response JSON")
            raise RuntimeError("Failed to parse Eagle API get-application-info response JSON")
        except Exception as e:
            # logger.error("An unexpected error occurred during get-application-info process", error=e)
            raise RuntimeError(f"An unexpected error occurred during get-application-info process: {e}")

    # TODO: Add other Eagle API methods later if needed (e.g., get_folders, move_to_trash)