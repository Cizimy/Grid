# nvt_ws/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

# プロジェクトルートからの相対パスを解決するためのベースパス
# 環境変数 BASE_DIR が設定されていればそれを使用、なければスクリプトの親の親をルートとする
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent.parent))
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_LOG_DIR = BASE_DIR / "logs"

class AppSettings(BaseSettings):
    default_ai_model: str = "nai-diffusion-3"

class ApiSettings(BaseSettings):
    novelai_api_key: str = Field(..., validation_alias='NOVELAI_API_KEY') # .envから読み込み
    eagle_api_host: str = "http://localhost:41595"

class DatabaseSettings(BaseSettings):
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_user: str | None = Field(None, validation_alias='NEO4J_USER') # .envから読み込み (任意)
    neo4j_password: str | None = Field(None, validation_alias='NEO4J_PASSWORD') # .envから読み込み (任意)

class PathSettings(BaseSettings):
    data_base_dir: Path = DEFAULT_DATA_DIR
    vibe_image_dir: str = "vibe"
    encoded_vibe_dir: str = "encoded"
    generated_image_dir: str = "generated"

    # 各データディレクトリへのフルパスをプロパティとして定義すると便利
    @property
    def vibe_dir(self) -> Path:
        path = self.data_base_dir / self.vibe_image_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def encoded_dir(self) -> Path:
        path = self.data_base_dir / self.encoded_vibe_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def generated_dir(self) -> Path:
        path = self.data_base_dir / self.generated_image_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

class LoggingSettings(BaseSettings):
    log_level: str = "INFO"
    log_file_path: Path = DEFAULT_LOG_DIR / "nvt_ws.log"
    log_rotation: str = "daily"
    log_retention: str = "7 days"

    # ログディレクトリ作成
    def __init__(self, **values):
        super().__init__(**values)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # 各セクションの設定を読み込む
    app: AppSettings = Field(default_factory=AppSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    # .envファイルとconfig.tomlから設定を読み込む設定
    # `pip install pydantic-settings toml` が必要
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        env_nested_delimiter='__',
        toml_file=BASE_DIR / 'config.toml',
        extra='ignore' # TOMLファイルに余分なキーがあっても無視
    )

# グローバル設定インスタンス (シングルトン的に使う)
settings = Settings()

# --- 使用例 ---
if __name__ == "__main__":
    print(f"NovelAI Key (Loaded from .env): {settings.api.novelai_api_key[:5]}...") # APIキー全体は表示しない
    print(f"Neo4j URI (Loaded from config.toml): {settings.database.neo4j_uri}")
    print(f"Default AI Model: {settings.app.default_ai_model}")
    print(f"Encoded Vibe Dir Path: {settings.paths.encoded_dir}")
    print(f"Log Level: {settings.logging.log_level}")
    print(f"Log File Path: {settings.logging.log_file_path}")