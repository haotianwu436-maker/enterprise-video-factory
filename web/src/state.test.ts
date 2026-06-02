import { describe, expect, it } from "vitest";
import { progressPercent, stageIndex } from "./state";

describe("studio state helpers", () => {
  it("maps known stages to stable positions", () => {
    expect(stageIndex("source_intake")).toBe(1);
    expect(stageIndex("release")).toBe(8);
  });

  it("marks publish-ready jobs as complete", () => {
    expect(progressPercent({ state: "publish_ready", active_stage: "release" } as any)).toBe(100);
  });
});
