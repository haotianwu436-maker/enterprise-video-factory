"""Deterministic generation pipeline and model adapters."""

from __future__ import annotations

import base64
import json
import os
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from video_factory_runtime.domain import Job, JobProgress
from video_factory_runtime.storage import SQLiteRuntimeStore


class GenerationBlocked(RuntimeError):
    """Raised when a required remote model service is unavailable."""


class CosyVoiceAdapter:
    """Remote CosyVoice service adapter."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.environ.get("COSYVOICE_BASE_URL")

    def synthesize(self, *, job: Job, output_dir: Path) -> Path:
        if not self.base_url:
            raise GenerationBlocked("COSYVOICE_BASE_URL is not configured")
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/v1/tts",
            json={
                "job_id": job.job_id,
                "tenant_id": job.tenant_id,
                "text": job.input_text,
                "voice_profile_id": _binding_asset(job, "voice_profile_id"),
                "duration_target_sec": job.duration_target_sec,
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        audio_path = output_dir / "voice.wav"
        if payload.get("audio_base64"):
            audio_path.write_bytes(base64.b64decode(payload["audio_base64"]))
        elif payload.get("audio_uri") and Path(str(payload["audio_uri"])).exists():
            audio_path.write_bytes(Path(str(payload["audio_uri"])).read_bytes())
        else:
            raise GenerationBlocked("CosyVoice response did not include audio_base64 or readable audio_uri")
        return audio_path


class MuseTalkAdapter:
    """Remote MuseTalk placeholder for future GPU workers."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.environ.get("MUSETALK_BASE_URL")

    def is_configured(self) -> bool:
        return bool(self.base_url)


class GenerationPipeline:
    """Run a local deterministic pipeline around remote model adapters."""

    def __init__(
        self,
        store: SQLiteRuntimeStore,
        *,
        data_dir: Path = Path("var/video_factory"),
        cosyvoice: CosyVoiceAdapter | None = None,
        musetalk: MuseTalkAdapter | None = None,
    ) -> None:
        self.store = store
        self.data_dir = data_dir
        self.cosyvoice = cosyvoice or CosyVoiceAdapter()
        self.musetalk = musetalk or MuseTalkAdapter()

    def start(self, tenant_id: str, job_id: str) -> dict[str, Any]:
        job = self.store.get(tenant_id, job_id)
        if not isinstance(job, Job):
            raise KeyError(job_id)
        if job.state in {"failed", "publish_ready", "cancelled"}:
            return job.to_api()
        job_dir = self.data_dir / tenant_id / "jobs" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        storyboard_path = self._plan(job, job_dir)
        job = self._transition(job, "planned", "planning", segments_total=6)
        self.store.save(job)
        self.store.save_artifact(
            tenant_id,
            {
                "job_id": job.job_id,
                "stage": "planning",
                "manifest_uri": str(storyboard_path),
                "qc_status": "passed",
                "file_uri": str(storyboard_path),
            },
        )

        try:
            audio_path = self.cosyvoice.synthesize(job=job, output_dir=job_dir)
        except Exception as exc:
            failed = self._transition(job, "failed", "tts")
            self.store.save(failed)
            self.store.save_qc_report(
                tenant_id,
                {
                    "job_id": job.job_id,
                    "stage": "tts",
                    "status": "failed_terminal",
                    "failure_codes": ["model_runtime_error"],
                    "message": str(exc),
                },
            )
            return failed.to_api()

        try:
            video_path = self._render_with_remotion(job, job_dir, audio_path)
        except Exception as exc:
            failed = self._transition(job, "failed", "scene_render")
            self.store.save(failed)
            self.store.save_qc_report(
                tenant_id,
                {
                    "job_id": job.job_id,
                    "stage": "scene_render",
                    "status": "failed_terminal",
                    "failure_codes": ["renderer_runtime_error"],
                    "message": str(exc),
                },
            )
            return failed.to_api()
        ready = self._transition(job, "publish_ready", "release", segments_completed=6)
        self.store.save(ready)
        self.store.save_artifact(
            tenant_id,
            {
                "job_id": job.job_id,
                "stage": "composition",
                "manifest_uri": str(video_path),
                "qc_status": "passed",
                "file_uri": str(video_path),
            },
        )
        self.store.save_qc_report(
            tenant_id,
            {
                "job_id": job.job_id,
                "stage": "qc",
                "status": "passed",
                "failure_codes": [],
                "message": "Local ffmpeg composition completed.",
            },
        )
        return ready.to_api()

    def _plan(self, job: Job, job_dir: Path) -> Path:
        words = [part for part in job.input_text.replace("。", "。|").split("|") if part.strip()]
        scenes = []
        for index in range(6):
            text = words[index % len(words)] if words else job.input_text
            scenes.append(
                {
                    "scene_id": f"scene_{index + 1:03d}",
                    "order": index + 1,
                    "duration_sec": 10,
                    "script": text.strip(),
                    "visual_mode": "creative_studio_fallback" if not self.musetalk.is_configured() else "musetalk_remote",
                }
            )
        path = job_dir / "storyboard.json"
        path.write_text(
            json.dumps(
                {
                    "job_id": job.job_id,
                    "tenant_id": job.tenant_id,
                    "target": {"duration_sec": 60, "aspect_ratio": "9:16", "resolution": [1080, 1920]},
                    "scenes": scenes,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def _render_with_remotion(self, job: Job, job_dir: Path, audio_path: Path) -> Path:
        props_path = job_dir / "remotion-props.json"
        scene_video = job_dir / "remotion-scene.mp4"
        final_video = job_dir / "final.mp4"
        storyboard = json.loads((job_dir / "storyboard.json").read_text(encoding="utf-8"))
        props_path.write_text(
            json.dumps(
                {
                    "jobId": job.job_id,
                    "title": "Enterprise Video Factory",
                    "script": job.input_text,
                    "scenes": storyboard["scenes"],
                    "durationSeconds": 60,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        render_cmd = [
            "npm",
            "run",
            "render:factory",
            "--",
            "--props",
            str(props_path.resolve()),
            "--output",
            str(scene_video.resolve()),
        ]
        subprocess.run(render_cmd, cwd=Path("web"), check=True, capture_output=True, text=True)
        mux_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(scene_video),
            "-i",
            str(audio_path),
            "-shortest",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(final_video),
        ]
        subprocess.run(mux_cmd, check=True, capture_output=True, text=True)
        return final_video

    def _transition(
        self,
        job: Job,
        state: str,
        stage: str,
        *,
        segments_total: int | None = None,
        segments_completed: int | None = None,
    ) -> Job:
        progress = JobProgress(
            segments_total=segments_total if segments_total is not None else job.progress.segments_total,
            segments_completed=segments_completed if segments_completed is not None else job.progress.segments_completed,
            repair_attempts=job.progress.repair_attempts,
        )
        history = tuple([*job.state_history, state])
        return replace(
            job,
            state=state,
            active_stage=stage,
            state_history=history,
            progress=progress,
            updated_at=datetime.now(timezone.utc),
        )


def _binding_asset(job: Job, field: str) -> str | None:
    for binding in job.asset_bindings:
        if binding.request_field == field:
            return binding.asset_id
    return None
