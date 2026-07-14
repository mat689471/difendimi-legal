import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Video,
  spring,
} from "remotion";

const FPS = 30;

// Animated text overlay with slide-in and fade
const AnimatedCaption: React.FC<{
  text: string;
  startFrame: number;
  durationFrames: number;
  style?: React.CSSProperties;
}> = ({ text, startFrame, durationFrames, style }) => {
  const frame = useCurrentFrame();
  const relFrame = frame - startFrame;

  const opacity = interpolate(
    relFrame,
    [0, 10, durationFrames - 15, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const translateY = interpolate(relFrame, [0, 15], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px)`,
        ...style,
      }}
    >
      {text}
    </div>
  );
};

// Pulsing call-to-action badge
const PulseBadge: React.FC<{ text: string; startFrame: number }> = ({
  text,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const relFrame = frame - startFrame;
  const scale = spring({ frame: relFrame, fps: FPS, config: { stiffness: 200, damping: 10 } });
  const pulse = 1 + 0.04 * Math.sin((relFrame * Math.PI * 2) / 30);

  return (
    <div
      style={{
        transform: `scale(${scale * pulse})`,
        background: "linear-gradient(135deg, #DC2626, #991B1B)",
        color: "white",
        fontFamily: "'Arial Black', Arial, sans-serif",
        fontWeight: 900,
        fontSize: 38,
        padding: "18px 40px",
        borderRadius: 60,
        textAlign: "center",
        boxShadow: "0 0 30px rgba(220,38,38,0.7), 0 4px 20px rgba(0,0,0,0.5)",
        letterSpacing: 1,
        textTransform: "uppercase",
      }}
    >
      {text}
    </div>
  );
};

// Flashing urgency bar
const UrgencyBar: React.FC<{ frame: number; text: string }> = ({ frame, text }) => {
  const flash = Math.floor(frame / 8) % 2 === 0;
  return (
    <div
      style={{
        background: flash ? "#DC2626" : "#7F1D1D",
        color: "white",
        width: "100%",
        padding: "14px 0",
        textAlign: "center",
        fontFamily: "'Arial Black', Arial, sans-serif",
        fontWeight: 900,
        fontSize: 28,
        letterSpacing: 3,
        textTransform: "uppercase",
        transition: "background 0.1s",
      }}
    >
      {text}
    </div>
  );
};

// Progress bar that fills over time
const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
  <div
    style={{
      position: "absolute",
      bottom: 0,
      left: 0,
      width: "100%",
      height: 6,
      background: "rgba(255,255,255,0.2)",
    }}
  >
    <div
      style={{
        height: "100%",
        width: `${progress * 100}%`,
        background: "linear-gradient(90deg, #DC2626, #F87171)",
        transition: "width 0.05s",
      }}
    />
  </div>
);

// Props della pipeline: tutto il CONTENUTO e' guidato dai dati, cosi' Jarvis
// puo' generare video diversi cambiando solo un brief (vedi jarvis/content).
export interface ViralVideoProps {
  brand: string;
  tagline: string;
  urgencyBar: string;
  captions: string[]; // le 7 didascalie centrali, per indice
  features: string[];
  ctaBadge: string;
  stores: string;
  hashtags: string;
}

export const defaultViralProps: ViralVideoProps = {
  brand: "⚖️ DIFENDIMI",
  tagline: "L'App che rende giustizia accessibile",
  urgencyBar: "⚠️ CONOSCI I TUOI DIRITTI ⚠️",
  captions: [
    "Sei stato fermato dalla polizia?",
    "Non sai cosa puoi e NON puoi fare? 🚫",
    "DIFENDIMI ti guida 24/7 con intelligenza artificiale 🤖",
    "", // slot 4: usa la lista features
    '"Finalmente posso difendermi da solo" 💬',
    "30 giorni GRATIS 🎁 Nessuna carta richiesta",
    "Scarica ora. La legge è dalla tua parte. ⚖️",
  ],
  features: [
    "✅ Diritti in tempo reale",
    "✅ Documenti legali gratis",
    "✅ Database leggi italiane",
  ],
  ctaBadge: "📲 Scarica DIFENDIMI",
  stores: "App Store  •  Google Play",
  hashtags: "#difendimi #diritti #italia #legge #giustizia",
};

export const ViralVideo: React.FC<Partial<ViralVideoProps>> = (rawProps) => {
  const p = { ...defaultViralProps, ...rawProps };
  const cap = (i: number) => p.captions[i] ?? defaultViralProps.captions[i];
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = frame / durationInFrames;

  // Zoom in slowly on the video (Ken Burns effect)
  const videoScale = interpolate(frame, [0, durationInFrames], [1.0, 1.12], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Overlay fade in
  const overlayOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "#000", fontFamily: "Arial, sans-serif" }}>
      {/* Background video with zoom */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale})`,
          transformOrigin: "center center",
        }}
      >
        <Video
          src={staticFile("video.webm")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          volume={0.25}
          loop
        />
      </AbsoluteFill>

      {/* Dark gradient overlay for text legibility */}
      <AbsoluteFill
        style={{
          opacity: overlayOpacity,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.1) 40%, rgba(0,0,0,0.1) 60%, rgba(0,0,0,0.75) 100%)",
        }}
      />

      {/* Music */}
      <Audio src={staticFile("music.wav")} volume={0.85} />

      {/* === TOP SECTION === */}
      <AbsoluteFill style={{ opacity: overlayOpacity }}>
        {/* Top urgency bar */}
        <div style={{ position: "absolute", top: 0, left: 0, width: "100%" }}>
          <UrgencyBar frame={frame} text={p.urgencyBar} />
        </div>

        {/* App logo / branding */}
        <Sequence from={15} durationInFrames={durationInFrames - 15}>
          <div
            style={{
              position: "absolute",
              top: 80,
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <AnimatedCaption
              text={p.brand}
              startFrame={15}
              durationFrames={durationInFrames - 15}
              style={{
                color: "white",
                fontFamily: "'Arial Black', Arial, sans-serif",
                fontWeight: 900,
                fontSize: 72,
                textShadow: "0 0 30px rgba(220,38,38,0.9), 0 4px 15px rgba(0,0,0,0.8)",
                letterSpacing: 4,
              }}
            />
          </div>
        </Sequence>

        {/* Tagline */}
        <Sequence from={30} durationInFrames={durationInFrames - 30}>
          <div
            style={{
              position: "absolute",
              top: 170,
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <AnimatedCaption
              text={p.tagline}
              startFrame={30}
              durationFrames={durationInFrames - 30}
              style={{
                color: "#FCA5A5",
                fontSize: 32,
                fontWeight: 600,
                textShadow: "0 2px 10px rgba(0,0,0,0.9)",
                letterSpacing: 1,
              }}
            />
          </div>
        </Sequence>

        {/* === MIDDLE CAPTIONS — appear sequentially === */}

        {/* Caption 1: Problem hook */}
        <Sequence from={60} durationInFrames={120}>
          <div
            style={{
              position: "absolute",
              top: "38%",
              left: 60,
              right: 60,
              textAlign: "center",
            }}
          >
            <AnimatedCaption
              text={cap(0)}
              startFrame={60}
              durationFrames={120}
              style={{
                color: "white",
                fontFamily: "'Arial Black', Arial, sans-serif",
                fontWeight: 900,
                fontSize: 52,
                textShadow: "0 0 20px rgba(0,0,0,0.9), 0 4px 12px rgba(0,0,0,0.8)",
                lineHeight: 1.2,
              }}
            />
          </div>
        </Sequence>

        {/* Caption 2: Agitate */}
        <Sequence from={195} durationInFrames={120}>
          <div
            style={{
              position: "absolute",
              top: "38%",
              left: 60,
              right: 60,
              textAlign: "center",
            }}
          >
            <AnimatedCaption
              text={cap(1)}
              startFrame={195}
              durationFrames={120}
              style={{
                color: "white",
                fontFamily: "'Arial Black', Arial, sans-serif",
                fontWeight: 900,
                fontSize: 48,
                textShadow: "0 0 20px rgba(0,0,0,0.9)",
                lineHeight: 1.2,
              }}
            />
          </div>
        </Sequence>

        {/* Caption 3: Solution */}
        <Sequence from={330} durationInFrames={150}>
          <div
            style={{
              position: "absolute",
              top: "35%",
              left: 60,
              right: 60,
              textAlign: "center",
            }}
          >
            <AnimatedCaption
              text={cap(2)}
              startFrame={330}
              durationFrames={150}
              style={{
                color: "white",
                fontFamily: "'Arial Black', Arial, sans-serif",
                fontWeight: 900,
                fontSize: 46,
                textShadow: "0 0 20px rgba(0,0,0,0.9)",
                lineHeight: 1.25,
              }}
            />
          </div>
        </Sequence>

        {/* Caption 4: Features highlight */}
        <Sequence from={495} durationInFrames={150}>
          <div
            style={{
              position: "absolute",
              top: "30%",
              left: 60,
              right: 60,
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              gap: 20,
            }}
          >
            {p.features.map(
              (feat, i) => (
                <Sequence key={i} from={495 + i * 25} durationInFrames={150 - i * 25}>
                  <AnimatedCaption
                    text={feat}
                    startFrame={495 + i * 25}
                    durationFrames={150 - i * 25}
                    style={{
                      color: "white",
                      fontSize: 40,
                      fontWeight: 700,
                      textShadow: "0 2px 12px rgba(0,0,0,0.9)",
                      background: "rgba(30,58,138,0.7)",
                      padding: "10px 24px",
                      borderRadius: 12,
                      backdropFilter: "blur(4px)",
                    }}
                  />
                </Sequence>
              )
            )}
          </div>
        </Sequence>

        {/* Caption 5: Social proof */}
        <Sequence from={660} durationInFrames={150}>
          <div
            style={{
              position: "absolute",
              top: "38%",
              left: 60,
              right: 60,
              textAlign: "center",
            }}
          >
            <AnimatedCaption
              text={cap(4)}
              startFrame={660}
              durationFrames={150}
              style={{
                color: "#FDE68A",
                fontStyle: "italic",
                fontSize: 42,
                fontWeight: 600,
                textShadow: "0 2px 12px rgba(0,0,0,0.9)",
                lineHeight: 1.3,
              }}
            />
          </div>
        </Sequence>

        {/* Caption 6: Discount urgency */}
        <Sequence from={825} durationInFrames={150}>
          <div
            style={{
              position: "absolute",
              top: "35%",
              left: 60,
              right: 60,
              textAlign: "center",
            }}
          >
            <AnimatedCaption
              text={cap(5)}
              startFrame={825}
              durationFrames={150}
              style={{
                color: "white",
                fontFamily: "'Arial Black', Arial, sans-serif",
                fontWeight: 900,
                fontSize: 48,
                textShadow: "0 0 20px rgba(220,38,38,0.8), 0 2px 12px rgba(0,0,0,0.9)",
                lineHeight: 1.25,
              }}
            />
          </div>
        </Sequence>

        {/* Caption 7: Final CTA */}
        <Sequence from={990} durationInFrames={durationInFrames - 990}>
          <div
            style={{
              position: "absolute",
              top: "35%",
              left: 60,
              right: 60,
              textAlign: "center",
            }}
          >
            <AnimatedCaption
              text={cap(6)}
              startFrame={990}
              durationFrames={durationInFrames - 990}
              style={{
                color: "white",
                fontFamily: "'Arial Black', Arial, sans-serif",
                fontWeight: 900,
                fontSize: 50,
                textShadow: "0 0 25px rgba(220,38,38,0.9), 0 4px 15px rgba(0,0,0,0.9)",
                lineHeight: 1.2,
              }}
            />
          </div>
        </Sequence>

        {/* === BOTTOM SECTION === */}

        {/* Pulse CTA badge (visible from midpoint onward) */}
        <Sequence from={495} durationInFrames={durationInFrames - 495}>
          <div
            style={{
              position: "absolute",
              bottom: 180,
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <PulseBadge text={p.ctaBadge} startFrame={495} />
          </div>
        </Sequence>

        {/* App Store badges text */}
        <Sequence from={600} durationInFrames={durationInFrames - 600}>
          <div
            style={{
              position: "absolute",
              bottom: 100,
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
              gap: 30,
            }}
          >
            <AnimatedCaption
              text={p.stores}
              startFrame={600}
              durationFrames={durationInFrames - 600}
              style={{
                color: "rgba(255,255,255,0.85)",
                fontSize: 26,
                fontWeight: 600,
                letterSpacing: 3,
                textShadow: "0 2px 8px rgba(0,0,0,0.8)",
              }}
            />
          </div>
        </Sequence>

        {/* Hashtags */}
        <Sequence from={750} durationInFrames={durationInFrames - 750}>
          <div
            style={{
              position: "absolute",
              bottom: 50,
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <AnimatedCaption
              text={p.hashtags}
              startFrame={750}
              durationFrames={durationInFrames - 750}
              style={{
                color: "rgba(252,165,165,0.9)",
                fontSize: 22,
                fontWeight: 500,
                letterSpacing: 1,
                textShadow: "0 1px 6px rgba(0,0,0,0.8)",
              }}
            />
          </div>
        </Sequence>

        {/* Progress bar */}
        <ProgressBar progress={progress} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
