import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BadgeCheck,
  Clapperboard,
  CloudUpload,
  Film,
  KeyRound,
  Library,
  LogIn,
  Play,
  ShieldCheck,
  Sparkles,
  Upload
} from "lucide-react";
import {
  apiGet,
  apiPost,
  buildCreateJobPayload,
  fileToBase64,
  login,
  MAX_UPLOAD_BYTES,
  type ArtifactSignedUrl,
  type Artifact,
  type Asset,
  type Job,
  type QcReport,
  type User
} from "./api";
import { pipelineStages, progressPercent } from "./state";

type ViewState = {
  token: string;
  user: User | null;
  assets: Asset[];
  jobs: Job[];
  selectedJob: Job | null;
  artifacts: Artifact[];
  artifactMediaUrl: string;
  qcReports: QcReport[];
};

const initialText = "企业级自动口播视频的关键不是一次生成，而是可恢复的流水线。";

export function App() {
  const [state, setState] = useState<ViewState>({
    token: localStorage.getItem("vf_token") ?? "",
    user: null,
    assets: [],
    jobs: [],
    selectedJob: null,
    artifacts: [],
    artifactMediaUrl: "",
    qcReports: []
  });
  const [email, setEmail] = useState("creator@example.local");
  const [password, setPassword] = useState("factory-demo");
  const [idea, setIdea] = useState(initialText);
  const [assetType, setAssetType] = useState("voice_profile");
  const [assetName, setAssetName] = useState("New authorized asset");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const bearer = state.token;
  const selectedJob = state.selectedJob ?? state.jobs[0] ?? null;
  const completion = progressPercent(selectedJob);

  useEffect(() => {
    if (bearer) void refreshAll(bearer);
  }, [bearer]);

  async function refreshAll(token = bearer, preferredJobId?: string) {
    if (!token) return;
    const [me, assets, jobs] = await Promise.all([
      apiGet<User>("/v1/auth/me", token),
      apiGet<{ assets: Asset[] }>("/v1/assets", token),
      apiGet<{ jobs: Job[] }>("/v1/jobs", token)
    ]);
    const currentJobId = preferredJobId ?? state.selectedJob?.job_id;
    const nextJob = jobs.jobs.find((job) => job.job_id === currentJobId) ?? jobs.jobs[0] ?? null;
    const [artifacts, qcReports] = nextJob
      ? await Promise.all([
          apiGet<{ artifacts: Artifact[] }>(`/v1/jobs/${nextJob.job_id}/artifacts`, token),
          apiGet<{ qc_reports: QcReport[] }>(`/v1/jobs/${nextJob.job_id}/qc`, token)
        ])
      : [{ artifacts: [] }, { qc_reports: [] }];
    const mediaUrl = nextJob ? await artifactMediaUrl(artifacts.artifacts, token) : "";
    setState((current) => ({
      ...current,
      user: me,
      assets: assets.assets,
      jobs: jobs.jobs,
      selectedJob: nextJob,
      artifacts: artifacts.artifacts,
      artifactMediaUrl: mediaUrl,
      qcReports: qcReports.qc_reports
    }));
  }

  async function handleLogin() {
    try {
      const result = await login(email, password);
      localStorage.setItem("vf_token", result.token);
      setState((current) => ({ ...current, token: result.token, user: result.user }));
      setMessage("登录成功，Studio 已连接运行时。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "登录失败");
    }
  }

  async function handleCreateAsset() {
    if (!bearer) return;
    try {
      const payload: Record<string, string> = { asset_type: assetType, display_name: assetName };
      if (file) {
        payload.file_name = file.name;
        payload.content_base64 = await fileToBase64(file);
      }
      const created = await apiPost<Asset>("/v1/assets", bearer, payload);
      if (created.asset_type === "voice_profile" || created.asset_type === "avatar_profile") {
        await apiPost(`/v1/assets/${created.asset_id}/consent`, bearer, {
          scope: {
            asset_id: created.asset_id,
            asset_type: created.asset_type,
            purpose: "talking-head video generation",
            holder: state.user?.email ?? "local creator"
          },
          evidence_uri: `local://studio-consent/${created.asset_id}/${Date.now()}`
        });
        await apiPost(`/v1/assets/${created.asset_id}/activate`, bearer);
      }
      setMessage("资产已登记并完成本地授权。");
      await refreshAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "资产登记失败");
    }
  }

  async function handleCreateJob() {
    if (!bearer) return;
    const job = await apiPost<Job>("/v1/jobs", bearer, buildCreateJobPayload(idea, state.assets));
    setState((current) => ({ ...current, selectedJob: job }));
    setMessage("Job 已创建，等待启动生成。");
    await refreshAll(bearer, job.job_id);
  }

  async function handleSelectJob(job: Job) {
    if (!bearer) return;
    const [artifacts, qcReports] = await Promise.all([
      apiGet<{ artifacts: Artifact[] }>(`/v1/jobs/${job.job_id}/artifacts`, bearer),
      apiGet<{ qc_reports: QcReport[] }>(`/v1/jobs/${job.job_id}/qc`, bearer)
    ]);
    const mediaUrl = await artifactMediaUrl(artifacts.artifacts, bearer);
    setState((current) => ({
      ...current,
      selectedJob: job,
      artifacts: artifacts.artifacts,
      artifactMediaUrl: mediaUrl,
      qcReports: qcReports.qc_reports
    }));
  }

  async function handleStartJob() {
    if (!bearer || !selectedJob) return;
    const job = await apiPost<Job>(`/v1/jobs/${selectedJob.job_id}/start`, bearer);
    setState((current) => ({ ...current, selectedJob: job }));
    setMessage(job.state === "failed" ? "生成已诚实失败：需要配置 COSYVOICE_BASE_URL。" : "生成完成。");
    await refreshAll(bearer, job.job_id);
  }

  const activeAssets = useMemo(() => state.assets.filter((asset) => asset.state === "active"), [state.assets]);

  if (!state.token) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <div className="brand-mark"><Sparkles size={30} /></div>
          <h1>Video Factory Studio</h1>
          <p>企业口播视频创作、授权资产和生成流水线的统一工作台。</p>
          <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button className="primary" onClick={handleLogin}><LogIn size={18} /> 登录 Studio</button>
          <small>默认账号 creator@example.local / factory-demo</small>
          {message && <div className="notice">{message}</div>}
        </section>
      </main>
    );
  }

  return (
    <main className="studio-shell">
      <aside className="rail">
        <div className="brand-mark"><Clapperboard size={28} /></div>
        <button title="Studio"><Sparkles /></button>
        <button title="Assets"><Library /></button>
        <button title="Jobs"><Activity /></button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Creative Studio</p>
            <h1>自动口播视频生产台</h1>
          </div>
          <div className="identity"><ShieldCheck size={18} /> {state.user?.email}</div>
        </header>

        <section className="studio-grid">
          <div className="composer">
            <div className="panel-head"><Sparkles size={18} /><span>观点输入</span></div>
            <textarea value={idea} onChange={(event) => setIdea(event.target.value)} />
            <div className="spec-row">
              <span>60s</span><span>9:16</span><span>1080×1920</span><span>CosyVoice</span>
            </div>
            <button className="primary" onClick={handleCreateJob}><Film size={18} /> 创建 Job</button>
            <button className="secondary" onClick={handleStartJob} disabled={!selectedJob}><Play size={18} /> 启动生成</button>
            {message && <div className="notice">{message}</div>}
          </div>

          <div className="preview-stage">
            <div className="phone-frame">
              {state.artifactMediaUrl ? (
                <video className="result-video" src={state.artifactMediaUrl} controls playsInline />
              ) : (
                <div className="video-preview">
                  <span className="preview-kicker">VIDEO FACTORY</span>
                  <h2>{selectedJob?.state ?? "ready"}</h2>
                  <p>{idea}</p>
                  <div className="waveform"><i /><i /><i /><i /><i /></div>
                </div>
              )}
            </div>
          </div>

          <div className="inspector">
            <div className="panel-head"><Activity size={18} /><span>Pipeline</span></div>
            <div className="meter"><div style={{ width: `${completion}%` }} /></div>
            <ol className="stage-list">
              {pipelineStages.map((stage) => (
                <li key={stage} className={selectedJob?.active_stage === stage ? "active" : ""}>
                  <BadgeCheck size={16} /> {stage}
                </li>
              ))}
            </ol>
            <div className="qc-box">
              <strong>QC</strong>
              {state.qcReports.length ? state.qcReports.map((report) => <p key={report.qc_report_id}>{report.status}: {report.message}</p>) : <p>等待生成证据。</p>}
            </div>
          </div>
        </section>

        <section className="lower-grid">
          <div className="asset-panel">
            <div className="panel-head"><CloudUpload size={18} /><span>资产授权</span></div>
            <div className="asset-form">
              <select value={assetType} onChange={(event) => setAssetType(event.target.value)}>
                <option value="voice_profile">Voice profile</option>
                <option value="avatar_profile">Avatar profile</option>
                <option value="brand_kit">Brand kit</option>
                <option value="music_asset">Music asset</option>
                <option value="template">Template</option>
              </select>
              <input value={assetName} onChange={(event) => setAssetName(event.target.value)} />
              <input
                type="file"
                accept=".wav,.mp3,.m4a,.mp4,.mov,.png,.jpg,.jpeg,.json"
                onChange={(event) => {
                  const nextFile = event.target.files?.[0] ?? null;
                  if (nextFile && nextFile.size > MAX_UPLOAD_BYTES) {
                    setMessage("文件超过本地 25MB 限制");
                    setFile(null);
                    return;
                  }
                  setFile(nextFile);
                }}
              />
              <button className="secondary" onClick={handleCreateAsset}><Upload size={16} /> 上传授权</button>
            </div>
            <div className="asset-list">
              {activeAssets.map((asset) => <span key={asset.asset_id}>{asset.asset_type} · {asset.asset_id}</span>)}
            </div>
          </div>

          <div className="timeline-panel">
            <div className="panel-head"><KeyRound size={18} /><span>Jobs & Artifacts</span></div>
            <div className="job-strip">
              {state.jobs.map((job) => (
                <button key={job.job_id} onClick={() => void handleSelectJob(job)}>
                  {job.job_id}<small>{job.state}</small>
                </button>
              ))}
            </div>
            <div className="artifact-list">
              {state.artifacts.map((artifact) => <span key={artifact.artifact_id}>{artifact.stage}: {artifact.qc_status}</span>)}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

async function artifactMediaUrl(artifacts: Artifact[], token: string): Promise<string> {
  const finalArtifact = artifacts.find((artifact) => artifact.stage === "composition" && artifact.file_uri?.endsWith(".mp4"));
  if (!finalArtifact) return "";
  const signed = await apiGet<ArtifactSignedUrl>(`/v1/artifacts/${finalArtifact.artifact_id}/signed-url`, token);
  return signed.url;
}
