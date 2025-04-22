# Grid Project

This is the repository for the Grid application, a tool to assist with NovelAI Vibe Transfer optimization.

## Development Environment Setup

This project uses Docker Compose for the Neo4j database and `pip` with `requirements.txt` for Python dependency management.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd cizimy-grid
    ```

2.  **Set up the Neo4j Database:**
    Ensure Docker is installed and running. Navigate to the project root directory (`cizimy-grid`) and run the following command to start the Neo4j container in the background:
    ```bash
    docker compose -f docker/docker-compose.yml up -d
    ```
    The database will be initialized with basic constraints and a default user on first startup based on the `docker/init/init.cypher` script.

3.  **Install Python Dependencies:**
    Ensure Python 3.9+ and `pip` are installed. Navigate to the project root directory (`cizimy-grid`) and install the required libraries using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys and Settings:**
    Copy the `.env.example` file (if provided later) or manually create a `.env` file in the project root. Add your NovelAI API key and any other necessary credentials. **Do not commit `.env` to Git.**
    ```dotenv
    # .env
    NOVELAI_API_KEY="your_novelai_api_key_here"
    # Add other sensitive settings here
    ```
    Review `config.toml` and `grid/config.py` for other application settings and adjust paths if necessary.

5.  **Run the Application:**
    (Instructions to run the application will be added later)

## Project Structure

```
cizimy-grid/
├── .env                    # APIキーなど (Git管理外)
├── .gitignore              # Git管理対象外設定
├── config.toml             # アプリケーション設定ファイル
├── docker-compose.yml      # Neo4j Docker Compose configuration
├── docker/
│   └── init/
│       └── init.cypher     # Neo4j initialization script
├── grid/                   # Main source code package
│   ├── __init__.py
│   ├── main.py             # Application entry point
│   ├── config.py           # Settings loading (Pydantic models)
│   ├── core/               # Business logic, service layer
│   │   ├── api/            # External API clients (NovelAI, Eagle)
│   │   ├── db/             # Database repositories (Neo4j operations)
│   │   ├── models/         # Data models (Pydantic etc.)
│   │   └── services/       # Core logic for features
│   ├── ui/                 # Flet UI code
│   │   ├── views/          # Screens (windows, tabs, panes)
│   │   └── controls/       # Custom UI controls (if any)
│   └── utils/              # Utility functions etc.
│       └── logger.py       # structlog configuration
├── data/                   # (Git ignored) Generated data storage
│   ├── encoded/            # Encoded Vibe data
│   ├── generated/          # Generated images
│   └── vibe/               # Source Vibe images (if copied)
├── logs/                   # (Git ignored) Log files
├── tests/                  # Test code
├── pyproject.toml          # (Optional) Poetry/PDM configuration (not used for dependency install in current setup)
└── README.md               # Project description, setup instructions
```

## License

(License information will be added later)