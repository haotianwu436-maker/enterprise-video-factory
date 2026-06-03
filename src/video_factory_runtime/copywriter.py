"""Guided copywriting service for nontechnical creators."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx


COPYWRITER_QUESTIONS = [
    {
        "id": "situation",
        "label": "你的情况",
        "prompt": "你是谁？你现在想讲什么？可以像聊天一样随便说。",
        "placeholder": "例：我是做企业培训的，想讲为什么老板要重视短视频自动化。",
        "required": True,
    },
    {
        "id": "audience",
        "label": "你想打动谁",
        "prompt": "这条视频主要给谁看？",
        "placeholder": "例：中小企业老板、运营负责人、销售团队。",
        "required": False,
    },
    {
        "id": "pain",
        "label": "他们的痛点",
        "prompt": "他们现在最烦、最卡、最想解决的问题是什么？",
        "placeholder": "例：每天想发短视频，但写稿、拍摄、剪辑太耗时间。",
        "required": False,
    },
    {
        "id": "offer",
        "label": "你的观点或方案",
        "prompt": "你希望观众相信什么，或者你能提供什么？",
        "placeholder": "例：把内容生产做成流程，一条观点就能自动生成口播视频。",
        "required": False,
    },
    {
        "id": "proof",
        "label": "可信细节",
        "prompt": "有没有案例、数字、经历或一句真实观察？",
        "placeholder": "例：过去一条视频要半天，现在十几分钟能跑完整流程。",
        "required": False,
    },
    {
        "id": "action",
        "label": "希望观众做什么",
        "prompt": "看完之后，希望他们评论、私信、预约，还是记住一个观点？",
        "placeholder": "例：评论“自动化”，我发你流程图。",
        "required": False,
    },
]


@dataclass(frozen=True)
class CopywriterResult:
    """Generated creator-facing copy."""

    mode: str
    title: str
    hook: str
    script: str
    beats: list[str]
    caption: str
    hashtags: list[str]
    notes: list[str]
    provider_error: str | None = None

    def to_api(self) -> dict[str, Any]:
        payload = {
            "mode": self.mode,
            "title": self.title,
            "hook": self.hook,
            "script": self.script,
            "beats": self.beats,
            "caption": self.caption,
            "hashtags": self.hashtags,
            "notes": self.notes,
        }
        if self.provider_error:
            payload["provider_error"] = self.provider_error
        return payload


class CopywriterService:
    """Generate social-ready talking-head scripts from a guided creator brief."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_COPYWRITER_MODEL", "gpt-5.2-mini")

    def prompts(self) -> dict[str, Any]:
        return {
            "questions": COPYWRITER_QUESTIONS,
            "tone_options": ["专业可信", "有冲击力", "亲和自然"],
            "duration_options_sec": [30, 45, 60],
        }

    def generate(self, payload: dict[str, Any]) -> CopywriterResult:
        brief = self._normalize_brief(payload)
        if not brief["situation"]:
            raise ValueError("situation is required")
        if self.api_key:
            try:
                return self._generate_with_openai(brief)
            except Exception as exc:  # pragma: no cover - covered through API fallback behavior
                local = self._generate_local(brief)
                return CopywriterResult(
                    mode="openai_failed_local_fallback",
                    title=local.title,
                    hook=local.hook,
                    script=local.script,
                    beats=local.beats,
                    caption=local.caption,
                    hashtags=local.hashtags,
                    notes=local.notes + ["OpenAI 连接失败，已先生成一版本地草稿。"],
                    provider_error=str(exc),
                )
        return self._generate_local(brief)

    def _normalize_brief(self, payload: dict[str, Any]) -> dict[str, str | int]:
        def clean(key: str, default: str = "") -> str:
            value = payload.get(key, default)
            return str(value).strip()

        duration = payload.get("duration_sec", 60)
        if not isinstance(duration, int) or duration not in {30, 45, 60}:
            duration = 60
        return {
            "situation": clean("situation"),
            "audience": clean("audience", "正在被这个问题困扰的人"),
            "pain": clean("pain", "他们知道要做，但总卡在执行上"),
            "offer": clean("offer", "用自动化流程把复杂工作变简单"),
            "proof": clean("proof", "真正的变化来自流程，而不是靠人硬扛"),
            "action": clean("action", "评论区告诉我你的情况"),
            "tone": clean("tone", "专业可信"),
            "duration_sec": duration,
        }

    def _generate_local(self, brief: dict[str, str | int]) -> CopywriterResult:
        audience = str(brief["audience"])
        pain = str(brief["pain"])
        offer = str(brief["offer"])
        proof = str(brief["proof"])
        action = str(brief["action"])
        situation = str(brief["situation"])

        hook = f"如果你也是{audience}，这件事一定要尽早想明白。"
        title = "别再用手工方式做内容生产"
        beats = [
            "用一个强钩子点出目标人群和痛点。",
            "把用户当前的低效状态说具体。",
            "提出一个反常识但可信的核心观点。",
            "给出流程化解决方案和行动指令。",
        ]
        script = "\n".join(
            [
                hook,
                f"很多人现在的问题不是不努力，而是被重复工作拖住了。{pain}。",
                f"我的观察是：{situation}。",
                f"真正该升级的不是某一个工具，而是整套内容生产流程。{offer}。",
                f"你会发现，写稿、录音、拍摄、字幕、剪辑这些步骤，不应该每次都从零开始。{proof}。",
                f"所以这条视频想提醒你：别再把时间花在机械执行上，把你的观点变成可以复用、可以批量生成的系统。",
                action,
            ]
        )
        caption = f"{title}。{offer}。"
        return CopywriterResult(
            mode="local_template",
            title=title,
            hook=hook,
            script=script,
            beats=beats,
            caption=caption,
            hashtags=["#口播视频", "#内容自动化", "#AI创作"],
            notes=["本地文案引擎已生成草稿；配置 OPENAI_API_KEY 后可切换为云端 LLM 生成。"],
        )

    def _generate_with_openai(self, brief: dict[str, str | int]) -> CopywriterResult:
        system_prompt = (
            "你是中文短视频口播文案导演。"
            "请根据用户情况生成适合 9:16 口播视频的中文爆款文案。"
            "要求：小白能懂，开头 3 秒有钩子，避免夸大承诺，适合直接用于企业口播。"
            "只返回 JSON，不要 Markdown。"
        )
        user_prompt = {
            "brief": brief,
            "required_json_shape": {
                "title": "短标题",
                "hook": "前三秒钩子",
                "script": "完整口播稿，按自然段换行",
                "beats": ["分镜/表达节奏 1", "分镜/表达节奏 2"],
                "caption": "发布文案",
                "hashtags": ["#标签"],
                "notes": ["给创作者的提醒"],
            },
        }
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
                ],
            },
            timeout=45,
        )
        response.raise_for_status()
        body = response.json()
        text = self._extract_response_text(body)
        data = json.loads(text)
        return CopywriterResult(
            mode="openai",
            title=str(data["title"]).strip(),
            hook=str(data["hook"]).strip(),
            script=str(data["script"]).strip(),
            beats=[str(item).strip() for item in data.get("beats", []) if str(item).strip()],
            caption=str(data.get("caption", "")).strip(),
            hashtags=[str(item).strip() for item in data.get("hashtags", []) if str(item).strip()],
            notes=[str(item).strip() for item in data.get("notes", []) if str(item).strip()],
        )

    def _extract_response_text(self, body: dict[str, Any]) -> str:
        if isinstance(body.get("output_text"), str):
            return str(body["output_text"]).strip()
        chunks: list[str] = []
        for item in body.get("output", []):
            for content in item.get("content", []):
                if isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        text = "\n".join(chunks).strip()
        if not text:
            raise ValueError("OpenAI response did not contain text")
        return text
