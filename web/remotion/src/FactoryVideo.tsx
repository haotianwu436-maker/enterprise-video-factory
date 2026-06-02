import type { CSSProperties } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

type Scene = {
  scene_id: string;
  order: number;
  duration_sec: number;
  script: string;
  visual_mode: string;
};

export type FactoryVideoProps = {
  jobId: string;
  title: string;
  script: string;
  durationSeconds: number;
  scenes: Scene[];
};

const colors = {
  ink: "#f8fafc",
  muted: "#cbd5e1",
  panel: "#111827",
  teal: "#14b8a6",
  amber: "#fbbf24",
  rust: "#b45309",
  blue: "#1d4ed8",
  line: "#334155"
};

export const FactoryVideo = ({ jobId, title, script, scenes }: FactoryVideoProps) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const progress = frame / Math.max(1, durationInFrames - 1);
  const sceneIndex = Math.min(scenes.length - 1, Math.floor((frame / fps) / 10));
  const scene = scenes[Math.max(0, sceneIndex)] ?? scenes[0];
  const entrance = spring({ frame, fps, config: { damping: 18, stiffness: 90 } });
  const headlineY = interpolate(entrance, [0, 1], [90, 0]);
  const facePulse = interpolate(Math.sin(frame / 10), [-1, 1], [0.94, 1.04]);

  return (
    <AbsoluteFill style={styles.stage}>
      <div style={styles.backgroundGrid} />
      <div style={{ ...styles.scanline, transform: `translateY(${progress * 1920}px)` }} />

      <div style={styles.header}>
        <div style={styles.brand}>{title}</div>
        <div style={styles.job}>{jobId}</div>
      </div>

      <div style={styles.avatarWrap}>
        <div style={{ ...styles.avatarHalo, transform: `scale(${facePulse})` }} />
        <div style={styles.avatar}>
          <div style={styles.face}>
            <span style={styles.eye} />
            <span style={styles.eye} />
          </div>
          <div style={styles.mouth} />
        </div>
      </div>

      <div style={{ ...styles.copyBlock, transform: `translateY(${headlineY}px)` }}>
        <div style={styles.kicker}>SCENE {String((scene?.order ?? 1)).padStart(2, "0")}</div>
        <div style={styles.script}>{fitText(scene?.script || script)}</div>
      </div>

      <div style={styles.timeline}>
        {scenes.slice(0, 6).map((item, index) => {
          const active = index === sceneIndex;
          return (
            <div key={item.scene_id} style={{ ...styles.scenePill, ...(active ? styles.scenePillActive : {}) }}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{item.visual_mode === "musetalk_remote" ? "MuseTalk" : "Studio"}</strong>
            </div>
          );
        })}
      </div>

      <div style={styles.progressTrack}>
        <div style={{ ...styles.progressFill, width: `${Math.round(progress * 100)}%` }} />
      </div>

      <div style={styles.caption}>
        <span>{fitText(script, 72)}</span>
      </div>
    </AbsoluteFill>
  );
};

function fitText(value: string, max = 58): string {
  return value.length > max ? `${value.slice(0, max - 1)}...` : value;
}

const styles: Record<string, CSSProperties> = {
  stage: {
    color: colors.ink,
    background: `linear-gradient(180deg, #0b1020 0%, #111827 48%, #0f172a 100%)`,
    fontFamily: "Inter, Arial, sans-serif",
    overflow: "hidden"
  },
  backgroundGrid: {
    position: "absolute",
    inset: 0,
    backgroundImage:
      "linear-gradient(rgba(148,163,184,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.09) 1px, transparent 1px)",
    backgroundSize: "90px 90px",
    opacity: 0.52
  },
  scanline: {
    position: "absolute",
    left: 0,
    right: 0,
    top: -220,
    height: 220,
    background: "linear-gradient(180deg, transparent, rgba(20,184,166,0.18), transparent)"
  },
  header: {
    position: "absolute",
    top: 86,
    left: 72,
    right: 72,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    color: colors.muted,
    fontSize: 30
  },
  brand: {
    color: colors.amber,
    fontWeight: 800,
    textTransform: "uppercase"
  },
  job: {
    color: colors.muted,
    border: `2px solid ${colors.line}`,
    borderRadius: 8,
    padding: "14px 20px",
    background: "rgba(15, 23, 42, 0.72)"
  },
  avatarWrap: {
    position: "absolute",
    top: 310,
    left: 210,
    right: 210,
    height: 580,
    display: "grid",
    placeItems: "center"
  },
  avatarHalo: {
    position: "absolute",
    width: 480,
    height: 480,
    borderRadius: "50%",
    background: `radial-gradient(circle, rgba(20,184,166,0.26), rgba(29,78,216,0.08) 58%, transparent 70%)`
  },
  avatar: {
    width: 330,
    height: 430,
    borderRadius: 8,
    background: `linear-gradient(180deg, ${colors.blue}, ${colors.panel})`,
    border: `4px solid ${colors.line}`,
    display: "grid",
    placeItems: "center",
    boxShadow: "0 42px 90px rgba(0,0,0,0.42)"
  },
  face: {
    width: 190,
    height: 190,
    borderRadius: "50%",
    background: "#e2e8f0",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: 48
  },
  eye: {
    width: 22,
    height: 22,
    borderRadius: "50%",
    background: colors.panel
  },
  mouth: {
    position: "absolute",
    width: 88,
    height: 18,
    borderRadius: 8,
    background: colors.rust,
    transform: "translateY(82px)"
  },
  copyBlock: {
    position: "absolute",
    left: 72,
    right: 72,
    top: 930,
    padding: 44,
    borderRadius: 8,
    background: "rgba(15, 23, 42, 0.84)",
    border: `3px solid ${colors.line}`
  },
  kicker: {
    color: colors.teal,
    fontSize: 34,
    fontWeight: 800,
    marginBottom: 22
  },
  script: {
    color: colors.ink,
    fontSize: 64,
    lineHeight: 1.22,
    fontWeight: 800
  },
  timeline: {
    position: "absolute",
    left: 72,
    right: 72,
    bottom: 250,
    display: "flex",
    gap: 14
  },
  scenePill: {
    flex: 1,
    borderRadius: 8,
    padding: 18,
    background: "rgba(15, 23, 42, 0.82)",
    border: `2px solid ${colors.line}`,
    display: "grid",
    gap: 8,
    color: colors.muted,
    fontSize: 24
  },
  scenePillActive: {
    color: colors.ink,
    background: "rgba(15, 118, 110, 0.72)",
    borderColor: colors.teal
  },
  progressTrack: {
    position: "absolute",
    left: 72,
    right: 72,
    bottom: 196,
    height: 16,
    borderRadius: 8,
    background: "rgba(148, 163, 184, 0.22)",
    overflow: "hidden"
  },
  progressFill: {
    height: "100%",
    background: colors.teal
  },
  caption: {
    position: "absolute",
    left: 72,
    right: 72,
    bottom: 72,
    minHeight: 80,
    borderRadius: 8,
    padding: "24px 30px",
    background: "rgba(2, 6, 23, 0.76)",
    color: colors.ink,
    fontSize: 36,
    lineHeight: 1.35,
    border: `2px solid ${colors.line}`
  }
};
