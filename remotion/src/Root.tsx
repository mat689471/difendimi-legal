import { Composition } from "remotion";
import { ViralVideo } from "./ViralVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DifendimiViral"
        component={ViralVideo}
        durationInFrames={1350} // 45s at 30fps
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
