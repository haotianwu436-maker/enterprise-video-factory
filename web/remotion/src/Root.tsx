import { Composition } from "remotion";
import { FactoryVideo, type FactoryVideoProps } from "./FactoryVideo";

const defaultProps: FactoryVideoProps = {
  jobId: "job_preview",
  title: "Enterprise Video Factory",
  script: "企业级自动口播视频的关键不是一次生成，而是可恢复的流水线。",
  durationSeconds: 60,
  scenes: [
    {
      scene_id: "scene_001",
      order: 1,
      duration_sec: 10,
      script: "企业级自动口播视频的关键不是一次生成，而是可恢复的流水线。",
      visual_mode: "creative_studio_fallback"
    }
  ]
};

export const Root = () => (
  <Composition
    id="FactoryVertical"
    component={FactoryVideo}
    durationInFrames={1800}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaultProps}
  />
);
