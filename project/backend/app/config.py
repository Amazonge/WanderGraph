from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM 提供商: deepseek / openai / ollama
    LLM_PROVIDER: str = "ollama"

    # 云端 API Key（有则用云端，无则自动降级到本地 Ollama）
    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # 本地 Ollama 配置
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen3:8b"

    # 高德地图
    AMAP_KEY: str = ""

    # MCP 服务
    FOOD_MCP_URL: str = "http://localhost:8001/sse"
    HOTEL_MCP_URL: str = "http://localhost:8003/sse"
    TICKET_MCP_URL: str = "http://localhost:8002/sse"

    # Redis 配置（可选，设为 false 则使用内存模式）
    USE_REDIS: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_KEY_PREFIX: str = "wandergraph"

    class Config:
        env_file = ".env"


settings = Settings()
