import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  BookOpenText,
  Check,
  ChevronRight,
  Clapperboard,
  CloudUpload,
  Film,
  KeyRound,
  Library,
  LogIn,
  Mic2,
  Music2,
  Palette,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Upload,
  UserRound
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

type Choice = {
  value: string;
  label: string;
};

const initialText = "企业做短视频，不该把时间浪费在重复剪辑上，而应该把内容生产做成可复用的自动流程。";

const toneChoices: Choice[] = [
  { value: "trusted", label: "专业可信" },
  { value: "energetic", label: "有冲击力" },
  { value: "warm", label: "亲和自然" }
];

const captionChoices: Choice[] = [
  { value: "bold", label: "醒目大字幕" },
  { value: "clean", label: "干净商务" },
  { value: "social", label: "短视频节奏" }
];

const musicChoices: Choice[] = [
  { value: "none", label: "无配乐" },
  { value: "light", label: "轻快背景" },
  { value: "cinematic", label: "发布会感" }
];

const assetOptions = [
  { value: "voice_profile", label: "我的声音", icon: Mic2, helper: "上传一段本人授权音频，用于语音克隆。" },
  { value: "avatar_profile", label: "数字人形象", icon: UserRound, helper: "上传头像、形象素材或自拍视频。" },
  { value: "brand_kit", label: "品牌风格", icon: Palette, helper: "上传品牌色、字体、logo 或模板文件。" },
  { value: "music_asset", label: "背景音乐", icon: Music2, helper: "上传可商用的配乐或音效。" }
];

const stageCopy: Record<string, { label: string; detail: string }> = {
  source_intake: { label: "读取内容", detail: "检查文案、素材和授权。" },
  planning: { label: "设计脚本", detail: "拆分口播结构、镜头和字幕节奏。" },
  tts: { label: "生成声音", detail: "用已授权声音合成旁白。" },
  avatar: { label: "生成形象", detail: "准备数字人画面和动作。" },
  scene_render: { label: "制作画面", detail: "渲染竖屏场景、动画和字幕。" },
  composition: { label: "合成视频", detail: "合并画面、声音、字幕和配乐。" },
  qc: { label: "质量检查", detail: "检查时长、比例、字幕和文件状态。" },
  release: { label: "准备发布", detail: "生成可下载的成片。" }
};

const stateCopy: Record<string, string> = {
  validated: "草稿已准备好",
  running: "正在生成",
  publish_ready: "成片已完成",
  failed: "需要处理",
  cancelled: "已取消"
};

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
  const [tone, setTone] = useState("trusted");
  const [captionStyle, setCaptionStyle] = useState("bold");
  const [musicMood, setMusicMood] = useState("light");
  const [assetType, setAssetType] = useState("voice_profile");
  const [assetName, setAssetName] = useState("我的授权素材");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const bearer = state.token;
  const selectedJob = state.selectedJob ?? state.jobs[0] ?? null;
  const completion = progressPercent(selectedJob);
  const activeAssets = useMemo(() => state.assets.filter((asset) => asset.state === "active"), [state.assets]);
  const activeByType = useMemo(
    () => Object.fromEntries(activeAssets.map((asset) => [asset.asset_type, asset])),
    [activeAssets]
  );
  const latestQcMessage = state.qcReports[0]?.message ?? "";
  const missingVoiceRuntime = latestQcMessage.includes("COSYVOICE_BASE_URL");
  const canCreate = idea.trim().length >= 8;
  const canStart = Boolean(selectedJob);
  const statusLabel = selectedJob ? stateCopy[selectedJob.state] ?? selectedJob.state : "还没有创建视频";
  const currentStage = selectedJob?.active_stage ?? "source_intake";

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
      setMessage("已进入创作台。");
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
      setMessage("素材已保存，并记录本地授权。");
      setFile(null);
      await refreshAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "素材保存失败");
    }
  }

  async function handleCreateJob() {
    if (!bearer || !canCreate) return;
    const enrichedIdea = `${idea.trim()}\n\n创作设置：语气=${labelFor(toneChoices, tone)}；字幕=${labelFor(captionChoices, captionStyle)}；配乐=${labelFor(musicChoices, musicMood)}。`;
    const job = await apiPost<Job>("/v1/jobs", bearer, buildCreateJobPayload(enrichedIdea, state.assets));
    setState((current) => ({ ...current, selectedJob: job }));
    setMessage("视频方案已准备好，可以开始生成。");
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
    setMessage(job.state === "failed" ? "生成没有完成：还需要连接语音服务。" : "成片已生成。");
    await refreshAll(bearer, job.job_id);
  }

  if (!state.token) {
    return (
      <main className="login-shell">
        <section className="login-panel" aria-label="登录创作台">
          <div className="brand-lockup">
            <div className="brand-mark"><Clapperboard size={26} /></div>
            <div>
              <p className="eyebrow">Video Factory</p>
              <h1>进入口播视频创作台</h1>
            </div>
          </div>
          <p className="login-copy">给运营、创始人和内容团队使用的自动视频工作台。登录后输入观点，选择声音和形象，就能生成 9:16 口播视频。</p>
          <label>邮箱<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>密码<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button className="primary wide" onClick={handleLogin}><LogIn size={18} /> 进入创作台</button>
          <small>本地演示账号：creator@example.local / factory-demo</small>
          {message && <div className="notice">{message}</div>}
        </section>
      </main>
    );
  }

  return (
    <main className="product-shell">
      <aside className="app-rail" aria-label="主导航">
        <div className="brand-mark"><Clapperboard size={24} /></div>
        <button className="rail-button active" title="创作"><Sparkles /></button>
        <button className="rail-button" title="素材"><Library /></button>
        <button className="rail-button" title="生成记录"><Activity /></button>
      </aside>

      <section className="creator-workspace">
        <header className="product-topbar">
          <div>
            <p className="eyebrow">Creative Studio</p>
            <h1>把一个观点变成口播视频</h1>
            <p>适合非技术人员的商业化创作流程：写内容、选角色、定风格、生成成片。</p>
          </div>
          <div className="identity"><ShieldCheck size={18} /> {state.user?.email}</div>
        </header>

        <section className="workflow-strip" aria-label="创作步骤">
          <Step index="01" title="写想法" detail="输入观点或粘贴文案" active />
          <Step index="02" title="选角色" detail="声音、形象和授权" done={Boolean(activeByType.voice_profile || activeByType.avatar_profile)} />
          <Step index="03" title="定风格" detail="字幕、语气和配乐" done />
          <Step index="04" title="生成发布" detail="预览、检查、下载" done={selectedJob?.state === "publish_ready"} />
        </section>

        <section className="creation-grid">
          <section className="creation-panel" aria-label="创作输入">
            <div className="section-heading">
              <div className="icon-tile teal"><BookOpenText size={18} /></div>
              <div>
                <h2>今天想讲什么？</h2>
                <p>一句观点也可以，系统会自动扩成 60 秒竖屏口播。</p>
              </div>
            </div>
            <textarea
              className="idea-box"
              value={idea}
              onChange={(event) => setIdea(event.target.value)}
              aria-label="口播观点"
            />
            <div className="choice-group" aria-label="语气">
              {toneChoices.map((choice) => (
                <button
                  key={choice.value}
                  className={tone === choice.value ? "choice active" : "choice"}
                  onClick={() => setTone(choice.value)}
                >
                  {choice.label}
                </button>
              ))}
            </div>

            <div className="settings-grid">
              <OptionPicker title="字幕样式" icon={<Palette size={17} />} choices={captionChoices} value={captionStyle} onChange={setCaptionStyle} />
              <OptionPicker title="配乐氛围" icon={<Music2 size={17} />} choices={musicChoices} value={musicMood} onChange={setMusicMood} />
            </div>

            <div className="action-row">
              <button className="primary" onClick={handleCreateJob} disabled={!canCreate}>
                <Film size={18} /> 准备视频方案
              </button>
              <button className="secondary" onClick={handleStartJob} disabled={!canStart}>
                <Play size={18} /> 开始生成
              </button>
            </div>
            {message && <div className="notice">{message}</div>}
          </section>

          <section className="phone-preview-area" aria-label="视频预览">
            <div className="preview-header">
              <div>
                <p className="eyebrow">Preview</p>
                <h2>{statusLabel}</h2>
              </div>
              <span>60s · 9:16 · 1080p</span>
            </div>
            <div className="phone-frame commercial">
              {state.artifactMediaUrl ? (
                <video className="result-video" src={state.artifactMediaUrl} controls playsInline />
              ) : (
                <div className="video-preview">
                  <span className="preview-kicker">VIDEO FACTORY</span>
                  <h3>{selectedJob ? statusLabel : "等待你的观点"}</h3>
                  <p>{idea}</p>
                  <div className="presenter">
                    <div className="presenter-head" />
                    <div className="presenter-body" />
                  </div>
                  <div className="caption-bar">自动字幕会出现在这里</div>
                </div>
              )}
            </div>
          </section>

          <section className="readiness-panel" aria-label="发布前检查">
            <div className="section-heading compact">
              <div className="icon-tile amber"><BadgeCheck size={18} /></div>
              <div>
                <h2>发布前检查</h2>
                <p>只显示需要你处理的事情。</p>
              </div>
            </div>
            <div className="readiness-list">
              <ReadinessItem ok={canCreate} title="内容已填写" detail={canCreate ? "可以生成脚本。" : "至少输入一句观点。"} />
              <ReadinessItem ok={Boolean(activeByType.voice_profile)} title="声音授权" detail={activeByType.voice_profile ? "已有可用声音。" : "建议上传本人授权音频。"} />
              <ReadinessItem ok={Boolean(activeByType.avatar_profile)} title="形象授权" detail={activeByType.avatar_profile ? "已有可用形象。" : "可以先用默认画面。"} />
              <ReadinessItem
                ok={!missingVoiceRuntime && selectedJob?.state !== "failed"}
                title="语音服务"
                detail={missingVoiceRuntime ? "还没连接 CosyVoice 服务。" : "本地创作台已连接。"}
                warning={missingVoiceRuntime}
              />
            </div>
            <div className={missingVoiceRuntime ? "human-error visible" : "human-error"}>
              <AlertTriangle size={18} />
              <div>
                <strong>为什么没有出成片？</strong>
                <p>当前前后端可用，但真实语音克隆服务还没连接。接上 Windows/GPU 上的 CosyVoice worker 后，这里会继续走到 MP4 成片。</p>
              </div>
            </div>
            <button className="ghost" onClick={() => void refreshAll()}><RefreshCw size={16} /> 刷新状态</button>
          </section>
        </section>

        <section className="operations-grid">
          <section className="asset-studio" aria-label="素材管理">
            <div className="section-heading compact">
              <div className="icon-tile blue"><CloudUpload size={18} /></div>
              <div>
                <h2>我的素材</h2>
                <p>上传前请确认声音、形象、音乐都有授权。</p>
              </div>
            </div>
            <div className="asset-type-grid">
              {assetOptions.map((option) => {
                const Icon = option.icon;
                const isActive = assetType === option.value;
                const savedAsset = activeByType[option.value];
                return (
                  <button
                    key={option.value}
                    className={isActive ? "asset-type active" : "asset-type"}
                    onClick={() => {
                      setAssetType(option.value);
                      setAssetName(option.label);
                    }}
                  >
                    <Icon size={18} />
                    <span>{option.label}</span>
                    <small>{savedAsset ? "已可用" : option.helper}</small>
                  </button>
                );
              })}
            </div>
            <div className="upload-row">
              <input value={assetName} onChange={(event) => setAssetName(event.target.value)} aria-label="素材名称" />
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
              <button className="secondary" onClick={handleCreateAsset}><Upload size={16} /> 保存素材</button>
            </div>
            <div className="asset-list">
              {activeAssets.length ? activeAssets.map((asset) => (
                <span key={asset.asset_id}>{humanAssetType(asset.asset_type)} · {asset.display_name ?? asset.asset_id}</span>
              )) : <p>还没有素材。可以先创建视频方案，后续再补声音和形象。</p>}
            </div>
          </section>

          <section className="job-history" aria-label="生成记录">
            <div className="section-heading compact">
              <div className="icon-tile violet"><KeyRound size={18} /></div>
              <div>
                <h2>最近生成</h2>
                <p>给运营看的记录在这里，技术细节折叠在下方。</p>
              </div>
            </div>
            <div className="job-list">
              {state.jobs.length ? state.jobs.map((job) => (
                <button
                  key={job.job_id}
                  className={selectedJob?.job_id === job.job_id ? "job-row active" : "job-row"}
                  onClick={() => void handleSelectJob(job)}
                >
                  <span>{stateCopy[job.state] ?? job.state}</span>
                  <small>{shortId(job.job_id)} · {stageCopy[job.active_stage]?.label ?? job.active_stage}</small>
                  <ChevronRight size={16} />
                </button>
              )) : <p className="empty-copy">还没有生成记录。</p>}
            </div>
            <details className="diagnostics">
              <summary>技术诊断</summary>
              <div className="meter"><div style={{ width: `${completion}%` }} /></div>
              <ol className="stage-list">
                {pipelineStages.map((stage) => (
                  <li key={stage} className={currentStage === stage ? "active" : ""}>
                    <BadgeCheck size={16} />
                    <span>{stageCopy[stage]?.label ?? stage}</span>
                    <small>{stageCopy[stage]?.detail}</small>
                  </li>
                ))}
              </ol>
              {state.qcReports.length ? state.qcReports.map((report) => (
                <p className="diagnostic-note" key={report.qc_report_id}>{report.status}: {humanQcMessage(report)}</p>
              )) : <p className="diagnostic-note">等待生成证据。</p>}
            </details>
          </section>
        </section>
      </section>
    </main>
  );
}

function Step({ index, title, detail, active = false, done = false }: { index: string; title: string; detail: string; active?: boolean; done?: boolean }) {
  return (
    <div className={active ? "workflow-step active" : "workflow-step"}>
      <span>{done ? <Check size={15} /> : index}</span>
      <strong>{title}</strong>
      <small>{detail}</small>
    </div>
  );
}

function OptionPicker({ title, icon, choices, value, onChange }: { title: string; icon: ReactNode; choices: Choice[]; value: string; onChange: (value: string) => void }) {
  return (
    <div className="option-picker">
      <div className="option-title">{icon}<span>{title}</span></div>
      <div className="option-buttons">
        {choices.map((choice) => (
          <button key={choice.value} className={value === choice.value ? "mini-choice active" : "mini-choice"} onClick={() => onChange(choice.value)}>
            {choice.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function ReadinessItem({ ok, title, detail, warning = false }: { ok: boolean; title: string; detail: string; warning?: boolean }) {
  return (
    <div className={ok ? "readiness-item ok" : warning ? "readiness-item warning" : "readiness-item"}>
      <span>{ok ? <Check size={15} /> : warning ? <AlertTriangle size={15} /> : <ChevronRight size={15} />}</span>
      <div>
        <strong>{title}</strong>
        <small>{detail}</small>
      </div>
    </div>
  );
}

function labelFor(choices: Choice[], value: string) {
  return choices.find((choice) => choice.value === value)?.label ?? value;
}

function shortId(id: string) {
  return id.replace(/^job_/, "").slice(0, 10);
}

function humanAssetType(type: string) {
  return assetOptions.find((option) => option.value === type)?.label ?? type;
}

function humanQcMessage(report: QcReport) {
  if (report.message.includes("COSYVOICE_BASE_URL")) {
    return "还没连接语音克隆服务。";
  }
  return report.message;
}

async function artifactMediaUrl(artifacts: Artifact[], token: string): Promise<string> {
  const finalArtifact = artifacts.find((artifact) => artifact.stage === "composition" && artifact.file_uri?.endsWith(".mp4"));
  if (!finalArtifact) return "";
  const signed = await apiGet<ArtifactSignedUrl>(`/v1/artifacts/${finalArtifact.artifact_id}/signed-url`, token);
  return signed.url;
}
