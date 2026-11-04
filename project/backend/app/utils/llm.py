import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..config import settings


def clean_response(text: str) -> str:
    """统一清理 LLM 原始输出，便于后续 JSON 解析 / 展示。

    本项目的 qwen3:8b 通过 Ollama 的 OpenAI 兼容接口调用，思考过程放在
    独立的 `reasoning` 字段，`content` 本身是干净答案，因此这里主要处理：
    1. markdown 代码块围栏 ```...```（qwen3 经常用 ```json 包裹 JSON）
    2. 首尾空白
    """
    if not text:
        return ""

    text = text.strip()

    # 去除 markdown 代码块围栏
    # 覆盖 ```json\n...\n``` 与单行 ```...``` 两种形态
    fence = re.compile(r"^\s*```(?:[a-zA-Z0-9_+-]*)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)
    m = fence.match(text)
    if m:
        text = m.group(1).strip()
    elif text.startswith("```"):
        # 兜底：去掉首行 ``` 和末尾 ```
        lines = text.split("\n")
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return text


def parse_json(text: str):
    """容错地把 LLM 文本解析成 Python 对象（dict / list）。

    qwen3:8b 的两类常见坏输出会导致普通 `json.loads` 直接失败、被各
    agent 的 `except` 吞掉从而静默回退空结果：
    1. 合法 JSON 后跟尾部垃圾（如多余的 `}}`、解释性文字）；
    2. markdown 围栏包裹（由 clean_response 处理）。

    这里先 clean_response 去围栏，再用 `JSONDecoder.raw_decode` 解析
    **第一个完整 JSON 值**并忽略其后任何字符；失败则返回 None，由调用方
    决定回退策略。
    """
    raw = clean_response(text).strip()
    if not raw:
        return None
    decoder = json.JSONDecoder()
    try:
        obj, _end = decoder.raw_decode(raw)
        return obj
    except json.JSONDecodeError:
        # 整体都不是合法 JSON（如纯自然语言）→ 返回 None
        return None


class LLMClient:
    """统一的 LLM 调用客户端，支持 OpenAI / DeepSeek / Ollama（本地）

    优先级：显式指定 > 有 API Key 的云端 > 本地 Ollama
    """

    def __init__(self, provider: str | None = None):
        self.provider = provider or self._detect_provider()
        self._client = self._create_client()
        print(f"[LLM] 使用: {self.provider} ({self._client.model_name})")

    def _detect_provider(self) -> str:
        """自动检测可用的 LLM 提供商"""
        # 1. 用户显式指定
        explicit = settings.LLM_PROVIDER.lower()
        if explicit in ("deepseek", "openai"):
            if explicit == "deepseek" and settings.DEEPSEEK_API_KEY:
                return "deepseek"
            if explicit == "openai" and settings.OPENAI_API_KEY:
                return "openai"

        # 2. 有 DeepSeek Key
        if settings.DEEPSEEK_API_KEY and not settings.DEEPSEEK_API_KEY.startswith("sk-xxx"):
            return "deepseek"

        # 3. 有 OpenAI Key
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-xxx"):
            return "openai"

        # 4. 降级到本地 Ollama
        return "ollama"

    def _create_client(self) -> ChatOpenAI:
        if self.provider == "deepseek":
            return ChatOpenAI(
                model="deepseek-chat",
                base_url="https://api.deepseek.com",
                api_key=settings.DEEPSEEK_API_KEY,
                temperature=0.7,
                max_tokens=4096,
            )
        elif self.provider == "openai":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.7,
                max_tokens=4096,
            )
        else:
            # Ollama：OpenAI 兼容接口
            return ChatOpenAI(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,     # http://localhost:11434/v1
                api_key="ollama",                       # Ollama 不需要真实 key，但字段必填
                temperature=0.7,
                max_tokens=4096,
            )

    async def invoke(self, system: str, user: str) -> str:
        """基础调用，返回已清理的字符串（去 markdown 围栏 / 空白）。

        调用方拿到结果后可直接 json.loads 或直接展示。
        """
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
        response = await self._client.ainvoke(messages)
        return clean_response(response.content)

    async def invoke_json(self, system: str, user: str) -> dict:
        """调用并返回 JSON dict（自动清理 markdown 围栏）"""
        prompt = f"{system}\n\n请仅回复 JSON 格式，不要包含 markdown 代码块标记或其他文字。"
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=user),
        ]
        response = await self._client.ainvoke(messages)
        text = clean_response(response.content)
        return json.loads(text)


_llm_client: LLMClient | None = None


def get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
