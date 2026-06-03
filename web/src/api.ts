export type User = {
  user_id: string;
  tenant_id: string;
  email: string;
  role: string;
};

export type Asset = {
  asset_id: string;
  tenant_id: string;
  asset_type: string;
  state: string;
  display_name?: string;
  authorization_snapshots: string[];
  file_uri?: string;
};

export type Job = {
  job_id: string;
  tenant_id: string;
  state: string;
  active_stage: string;
  progress: { segments_total: number; segments_completed: number; repair_attempts: number };
  asset_authorization_snapshots: string[];
  state_history: string[];
};

export type QcReport = {
  qc_report_id: string;
  job_id: string;
  stage: string;
  status: string;
  failure_codes: string[];
  message: string;
};

export type Artifact = {
  artifact_id: string;
  job_id: string;
  stage: string;
  manifest_uri: string;
  qc_status?: string;
  file_uri?: string;
};

export type ArtifactSignedUrl = {
  url: string;
  expires_at: string;
};

export type CopywriterQuestion = {
  id: string;
  label: string;
  prompt: string;
  placeholder: string;
  required: boolean;
};

export type CopywriterPrompts = {
  questions: CopywriterQuestion[];
  tone_options: string[];
  duration_options_sec: number[];
};

export type CopywriterBrief = {
  situation: string;
  audience: string;
  pain: string;
  offer: string;
  proof: string;
  action: string;
  tone: string;
  duration_sec: number;
};

export type CopywriterResult = {
  mode: string;
  title: string;
  hook: string;
  script: string;
  beats: string[];
  caption: string;
  hashtags: string[];
  notes: string[];
  provider_error?: string;
};

const API_BASE = "";
export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  const response = await fetch(`${API_BASE}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) throw new Error("登录失败");
  const body = await response.json();
  return { token: body.access_token, user: body.user };
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiPost<T>(path: string, token: string, payload?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: payload === undefined ? undefined : JSON.stringify(payload)
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function fileToBase64(file: File): Promise<string> {
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error("文件超过本地 25MB 限制");
  }
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
  return dataUrl.split(",", 2)[1] ?? "";
}

export function buildCreateJobPayload(text: string, assets: Asset[]) {
  const byType = Object.fromEntries(assets.filter((asset) => asset.state === "active").map((asset) => [asset.asset_type, asset]));
  return {
    input: { type: "opinion", text },
    asset_refs: {
      voice_profile_id: byType.voice_profile?.asset_id ?? "voice_abc",
      avatar_profile_id: byType.avatar_profile?.asset_id ?? "avatar_def",
      template_id: byType.template?.asset_id ?? "template_001",
      music_asset_id: byType.music_asset?.asset_id ?? "music_001",
      brand_kit_id: byType.brand_kit?.asset_id ?? "brand_001"
    },
    output_profile: { duration_target_sec: 60, aspect_ratio: "9:16" }
  };
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}
