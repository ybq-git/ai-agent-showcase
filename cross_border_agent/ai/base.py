from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class LLMMessage:
    role: str
    content: str

@dataclass
class LLMResponse:
    content: str            # 模型回答的文本
    raw: dict = None        # 模型返回的原始数据(可能没有)
    
class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self,messages:list[LLMMessage]) ->LLMResponse:
        ...