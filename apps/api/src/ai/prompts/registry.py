from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.models import PromptVersion


class PromptRegistry:
    """Manages versioned prompt templates stored in the database."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_prompt(
        self, prompt_id: str
    ) -> PromptVersion | None:
        result = await self.db.execute(
            select(PromptVersion)
            .where(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.is_active == True,  # noqa: E712
            )
            .order_by(PromptVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_prompt_by_version(
        self, prompt_id: str, version: int
    ) -> PromptVersion | None:
        result = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def create_version(
        self,
        prompt_id: str,
        template_text: str,
        system_prompt: str | None = None,
        description: str | None = None,
        ai_model: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> PromptVersion:
        # Get next version number
        result = await self.db.execute(
            select(PromptVersion.version)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        next_version = (latest or 0) + 1

        prompt = PromptVersion(
            prompt_id=prompt_id,
            version=next_version,
            template_text=template_text,
            system_prompt=system_prompt,
            description=description,
            ai_model=ai_model,
            parameters=parameters,
        )
        self.db.add(prompt)
        await self.db.flush()
        await self.db.refresh(prompt)
        return prompt

    async def list_prompts(self) -> list[PromptVersion]:
        result = await self.db.execute(
            select(PromptVersion)
            .where(PromptVersion.is_active == True)  # noqa: E712
            .order_by(PromptVersion.prompt_id, PromptVersion.version.desc())
        )
        return list(result.scalars().all())
