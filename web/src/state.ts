import type { Job } from "./api";

export const pipelineStages = [
  "source_intake",
  "planning",
  "tts",
  "avatar",
  "scene_render",
  "composition",
  "qc",
  "release"
];

export function progressPercent(job?: Job | null): number {
  if (!job) return 0;
  if (job.state === "publish_ready") return 100;
  if (job.state === "failed") return Math.max(12, stageIndex(job.active_stage) * 12);
  return Math.min(96, Math.max(8, stageIndex(job.active_stage) * 12));
}

export function stageIndex(stage: string): number {
  const index = pipelineStages.indexOf(stage);
  return index < 0 ? 1 : index + 1;
}
