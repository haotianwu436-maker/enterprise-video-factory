import { afterEach, describe, expect, it, vi } from "vitest";
import { buildAssetPreviewUrls, buildCreateJobPayload, firstActiveAssetByType } from "./api";
import { progressPercent, stageIndex } from "./state";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("studio state helpers", () => {
  it("maps known stages to stable positions", () => {
    expect(stageIndex("source_intake")).toBe(1);
    expect(stageIndex("release")).toBe(8);
  });

  it("marks publish-ready jobs as complete", () => {
    expect(progressPercent({ state: "publish_ready", active_stage: "release" } as any)).toBe(100);
  });

  it("builds signed previews only for image assets", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ url: "/v1/assets/avatar_1/media?token=preview", expires_at: "2026-06-03T00:00:00Z" })
    }));
    vi.stubGlobal("fetch", fetchMock);

    const previews = await buildAssetPreviewUrls(
      [
        {
          asset_id: "avatar_1",
          tenant_id: "tenant_123",
          asset_type: "avatar_profile",
          state: "active",
          authorization_snapshots: [],
          file_uri: "var/video_factory/tenant_123/assets/avatar.jpg"
        },
        {
          asset_id: "voice_1",
          tenant_id: "tenant_123",
          asset_type: "voice_profile",
          state: "active",
          authorization_snapshots: [],
          file_uri: "var/video_factory/tenant_123/assets/voice.wav"
        }
      ],
      "token_123"
    );

    expect(previews.avatar_1).toContain("/v1/assets/avatar_1/media");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith("/v1/assets/avatar_1/signed-url", {
      headers: { Authorization: "Bearer token_123" }
    });
  });

  it("prefers the first active asset of each type when creating jobs", () => {
    const assets = [
      {
        asset_id: "avatar_real",
        tenant_id: "tenant_123",
        asset_type: "avatar_profile",
        state: "active",
        authorization_snapshots: []
      },
      {
        asset_id: "avatar_default",
        tenant_id: "tenant_123",
        asset_type: "avatar_profile",
        state: "active",
        authorization_snapshots: []
      },
      {
        asset_id: "voice_real",
        tenant_id: "tenant_123",
        asset_type: "voice_profile",
        state: "active",
        authorization_snapshots: []
      }
    ];

    expect(firstActiveAssetByType(assets).avatar_profile?.asset_id).toBe("avatar_real");
    expect(buildCreateJobPayload("真实头像应进入任务", assets).asset_refs.avatar_profile_id).toBe("avatar_real");
  });
});
