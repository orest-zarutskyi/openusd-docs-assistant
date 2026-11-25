import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ANSWERED, CORPUS, GATE, METRICS, PIPELINE, REFUSED, REPO } from "./data";

const C = {
  bg: "#0b0f17",
  panel: "rgba(18, 24, 38, 0.86)",
  border: "#243044",
  text: "#e6eaf2",
  muted: "#93a1b8",
  teal: "#2dd4bf",
  green: "#34d399",
  orange: "#fb923c",
};
const SANS = '"Segoe UI", "Inter", system-ui, sans-serif';
const MONO = '"Cascadia Code", Consolas, "JetBrains Mono", monospace';

// Scene timing in frames at 30 fps.
const SCENES = {
  intro: { from: 0, len: 135 },
  pipeline: { from: 135, len: 210 },
  answered: { from: 345, len: 345 },
  refused: { from: 690, len: 210 },
  metrics: { from: 900, len: 195 },
};
export const DURATION = SCENES.metrics.from + SCENES.metrics.len;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.22, 1, 0.36, 1);

const appear = (frame: number, start: number, len = 18) =>
  interpolate(frame, [start, start + len], [0, 1], { ...clamp, easing: ease });

const Fade: React.FC<{ len: number; children: React.ReactNode }> = ({ len, children }) => {
  const frame = useCurrentFrame();
  const opacity = Math.min(
    interpolate(frame, [0, 12], [0, 1], clamp),
    interpolate(frame, [len - 14, len], [1, 0], clamp),
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const x = 50 + 22 * Math.sin(t * 0.21);
  const y = 45 + 18 * Math.cos(t * 0.17);
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${x}% ${y}%, rgba(45,212,191,0.16), transparent 45%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          backgroundPosition: `0px ${-(frame * 0.4) % 64}px`,
        }}
      />
    </AbsoluteFill>
  );
};

const Panel: React.FC<{ style?: React.CSSProperties; children: React.ReactNode }> = ({
  style,
  children,
}) => (
  <div
    style={{
      background: C.panel,
      border: `1px solid ${C.border}`,
      borderRadius: 20,
      boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
      ...style,
    }}
  >
    {children}
  </div>
);

const Typewriter: React.FC<{ text: string; start: number; cps?: number; style?: React.CSSProperties }> = ({
  text,
  start,
  cps = 34,
  style,
}) => {
  const frame = useCurrentFrame();
  const end = start + (text.length / cps) * 30;
  const shown = Math.floor(interpolate(frame, [start, end], [0, text.length], clamp));
  const typing = frame < end + 20;
  const cursorOn = Math.floor(frame / 8) % 2 === 0;
  return (
    <span style={style}>
      {text.slice(0, shown)}
      {typing ? (
        <span style={{ color: C.teal, opacity: cursorOn ? 1 : 0 }}>▍</span>
      ) : null}
    </span>
  );
};

const typingEnd = (text: string, start: number, cps = 34) => start + (text.length / cps) * 30;

const Ask: React.FC<{ question: string; start: number }> = ({ question, start }) => {
  const frame = useCurrentFrame();
  const a = appear(frame, start - 10);
  return (
    <Panel style={{ padding: "28px 40px", opacity: a, transform: `translateY(${(1 - a) * 24}px)` }}>
      <div style={{ fontFamily: MONO, fontSize: 26, color: C.teal, marginBottom: 12 }}>
        POST /ask
      </div>
      <Typewriter
        text={question}
        start={start}
        style={{ fontFamily: SANS, fontSize: 46, fontWeight: 600, color: C.text, lineHeight: 1.25 }}
      />
    </Panel>
  );
};

// Horizontal scale of the reranker's top score with the refusal gate marked.
const GateMeter: React.FC<{ score: number; start: number }> = ({ score, start }) => {
  const frame = useCurrentFrame();
  const lo = -10;
  const hi = 2;
  const pos = (v: number) => ((v - lo) / (hi - lo)) * 100;
  const a = appear(frame, start - 8);
  const sweep = interpolate(frame, [start, start + 40], [hi - 0.5, score], {
    ...clamp,
    easing: Easing.bezier(0.33, 1, 0.68, 1),
  });
  const done = frame >= start + 40;
  const pass = score >= GATE;
  const color = done ? (pass ? C.green : C.orange) : C.text;
  return (
    <Panel style={{ padding: "30px 40px 36px", opacity: a }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: SANS }}>
        <span style={{ fontSize: 28, color: C.muted }}>Top reranker score</span>
        <span style={{ fontFamily: MONO, fontSize: 34, color, fontWeight: 600 }}>
          {done ? score.toFixed(2) : "…"}
        </span>
      </div>
      <div style={{ position: "relative", height: 70, marginTop: 26 }}>
        <div
          style={{
            position: "absolute",
            top: 30,
            left: 0,
            right: 0,
            height: 10,
            borderRadius: 5,
            background: `linear-gradient(90deg, rgba(251,146,60,0.35) 0%, rgba(251,146,60,0.35) ${pos(GATE)}%, rgba(52,211,153,0.35) ${pos(GATE)}%, rgba(52,211,153,0.35) 100%)`,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: `${pos(GATE)}%`,
            top: 6,
            width: 3,
            height: 58,
            background: C.text,
            transform: "translateX(-50%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: `${pos(GATE)}%`,
            top: -30,
            transform: "translateX(-50%)",
            fontFamily: MONO,
            fontSize: 20,
            color: C.muted,
            whiteSpace: "nowrap",
          }}
        >
          gate {GATE.toFixed(2)}
        </div>
        <div
          style={{
            position: "absolute",
            left: `${pos(sweep)}%`,
            top: 17,
            width: 36,
            height: 36,
            borderRadius: 18,
            background: color,
            boxShadow: `0 0 24px ${color}`,
            transform: "translateX(-50%)",
          }}
        />
      </div>
      <div
        style={{
          fontFamily: SANS,
          fontSize: 26,
          color: pass ? C.green : C.orange,
          opacity: appear(frame, start + 42, 12),
          marginTop: 8,
        }}
      >
        {pass ? "Above the gate: the model gets 8 excerpts" : "Below the gate: refuse before calling the model"}
      </div>
    </Panel>
  );
};

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div
        style={{
          fontSize: 120,
          fontWeight: 700,
          color: C.text,
          letterSpacing: -2,
          transform: `translateY(${(1 - s) * 40}px)`,
          opacity: s,
        }}
      >
        OpenUSD Docs <span style={{ color: C.teal }}>Assistant</span>
      </div>
      <div
        style={{
          fontSize: 44,
          color: C.muted,
          marginTop: 18,
          opacity: appear(frame, 18),
          transform: `translateY(${(1 - appear(frame, 18)) * 20}px)`,
        }}
      >
        Answers that cite exact source lines, or an honest refusal
      </div>
      <div style={{ display: "flex", gap: 18, marginTop: 56 }}>
        {CORPUS.map((c, i) => {
          const a = appear(frame, 40 + i * 7);
          return (
            <div
              key={c}
              style={{
                fontFamily: MONO,
                fontSize: 26,
                color: C.teal,
                border: `1px solid ${C.border}`,
                background: C.panel,
                borderRadius: 999,
                padding: "10px 26px",
                opacity: a,
                transform: `scale(${0.8 + 0.2 * a})`,
              }}
            >
              {c}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Pipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = PIPELINE.length;
  const width = 196;
  const gap = 26;
  const total = n * width + (n - 1) * gap;
  const left = (1920 - total) / 2;
  const lineProgress = interpolate(frame, [20, 20 + n * 9], [0, 1], clamp);
  const packet = interpolate(frame, [110, 180], [0, 1], { ...clamp, easing: Easing.inOut(Easing.quad) });
  const active = Math.floor(packet * (n - 1) + 0.5);
  return (
    <AbsoluteFill style={{ fontFamily: SANS }}>
      <div
        style={{
          position: "absolute",
          top: 190,
          width: "100%",
          textAlign: "center",
          fontSize: 64,
          fontWeight: 700,
          color: C.text,
          opacity: appear(frame, 0),
        }}
      >
        How an answer is made
      </div>
      <div
        style={{
          position: "absolute",
          top: 300,
          width: "100%",
          textAlign: "center",
          fontSize: 32,
          color: C.muted,
          opacity: appear(frame, 8),
        }}
      >
        Every step runs locally except the optional Gemini model
      </div>
      <div
        style={{
          position: "absolute",
          left: left + width / 2,
          top: 540,
          height: 4,
          width: (total - width) * lineProgress,
          background: `linear-gradient(90deg, ${C.teal}, rgba(45,212,191,0.3))`,
          borderRadius: 2,
        }}
      />
      {PIPELINE.map((node, i) => {
        const s = spring({ frame: frame - 14 - i * 9, fps, config: { damping: 14, stiffness: 120 } });
        const lit = frame >= 110 && i <= active;
        return (
          <div
            key={node.label}
            style={{
              position: "absolute",
              left: left + i * (width + gap),
              top: 470,
              width,
              height: 140,
              borderRadius: 18,
              background: C.panel,
              border: `2px solid ${lit ? C.teal : C.border}`,
              boxShadow: lit ? "0 0 30px rgba(45,212,191,0.35)" : "none",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
              transform: `scale(${s})`,
              opacity: Math.min(1, s * 1.5),
            }}
          >
            <div style={{ fontSize: 30, fontWeight: 600, color: C.text, textAlign: "center" }}>
              {node.label}
            </div>
            {node.note ? (
              <div style={{ fontFamily: MONO, fontSize: 18, color: C.muted, marginTop: 8, textAlign: "center" }}>
                {node.note}
              </div>
            ) : null}
          </div>
        );
      })}
      <div
        style={{
          position: "absolute",
          left: left + width / 2 + (total - width) * packet - 14,
          top: 528,
          width: 28,
          height: 28,
          borderRadius: 14,
          background: C.teal,
          boxShadow: `0 0 30px ${C.teal}`,
          opacity: frame >= 106 && frame <= 186 ? 1 : 0,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 700,
          width: "100%",
          textAlign: "center",
          fontSize: 34,
          color: C.text,
          opacity: appear(frame, 150),
        }}
      >
        An answer ships only if <span style={{ color: C.teal }}>every quote</span> is found in the chunk it cites
      </div>
    </AbsoluteFill>
  );
};

const SourceCard: React.FC<{ source: (typeof ANSWERED.sources)[number]; start: number }> = ({
  source,
  start,
}) => {
  const frame = useCurrentFrame();
  const a = appear(frame, start, 20);
  return (
    <Panel
      style={{
        padding: "22px 32px",
        opacity: a,
        transform: `translateX(${(1 - a) * 120}px)`,
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 18, fontFamily: MONO }}>
        <span style={{ color: C.teal, fontSize: 28 }}>{source.path}</span>
        <span style={{ color: C.text, fontSize: 24 }}>{source.lines}</span>
        <span style={{ color: C.muted, fontSize: 22, fontFamily: SANS }}>{source.title}</span>
        <span style={{ marginLeft: "auto", color: C.green, fontSize: 24, fontFamily: SANS, opacity: appear(frame, start + 22, 10) }}>
          ✓ quote verified
        </span>
      </div>
      <div style={{ fontFamily: SANS, fontSize: 27, color: C.muted, lineHeight: 1.35 }}>
        “{source.quote}”
      </div>
    </Panel>
  );
};

const Answered: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const qEnd = typingEnd(ANSWERED.question, 12);
  const meterStart = qEnd + 10;
  const answerStart = meterStart + 62;
  const pop = spring({ frame: frame - answerStart, fps, config: { damping: 12, stiffness: 140 } });
  return (
    <AbsoluteFill style={{ padding: "60px 110px", gap: 26, display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <Ask question={ANSWERED.question} start={12} />
      <div style={{ display: "flex", gap: 26 }}>
        <div style={{ flex: 1.35 }}>
          <GateMeter score={ANSWERED.rerankScore} start={meterStart} />
        </div>
        <Panel
          style={{
            flex: 1,
            padding: "26px 40px",
            opacity: Math.min(1, pop * 1.4),
            transform: `scale(${0.85 + 0.15 * pop})`,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 24, color: C.green }}>status: answer</div>
          <div style={{ fontFamily: SANS, fontSize: 96, fontWeight: 700, color: C.text, lineHeight: 1.1 }}>
            {ANSWERED.answer}
          </div>
          <div style={{ fontFamily: SANS, fontSize: 24, color: C.muted }}>qwen3:4b on Ollama, with 3 sources</div>
        </Panel>
      </div>
      {ANSWERED.sources.map((s, i) => (
        <SourceCard key={s.path} source={s} start={answerStart + 20 + i * 16} />
      ))}
    </AbsoluteFill>
  );
};

const Refused: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const qEnd = typingEnd(REFUSED.question, 12);
  const meterStart = qEnd + 8;
  const resultStart = meterStart + 58;
  const pop = spring({ frame: frame - resultStart, fps, config: { damping: 14, stiffness: 140 } });
  return (
    <AbsoluteFill style={{ padding: "60px 110px", gap: 26, display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <Ask question={REFUSED.question} start={12} />
      <GateMeter score={REFUSED.rerankScore} start={meterStart} />
      <Panel
        style={{
          padding: "30px 40px",
          opacity: Math.min(1, pop * 1.4),
          transform: `translateY(${(1 - pop) * 30}px)`,
          borderColor: "rgba(251,146,60,0.5)",
        }}
      >
        <div style={{ fontFamily: MONO, fontSize: 30, color: C.orange }}>status: {REFUSED.status}</div>
        <div style={{ fontFamily: SANS, fontSize: 38, color: C.text, marginTop: 12, lineHeight: 1.3 }}>
          {REFUSED.answer}
        </div>
        <div style={{ fontFamily: SANS, fontSize: 28, color: C.muted, marginTop: 16, opacity: appear(frame, resultStart + 20) }}>
          {REFUSED.seconds} s end to end · the model was never called · no sources returned
        </div>
      </Panel>
    </AbsoluteFill>
  );
};

const Metrics: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ fontFamily: SANS, alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontSize: 64, fontWeight: 700, color: C.text, opacity: appear(frame, 0) }}>
        Measured, not claimed
      </div>
      <div style={{ fontSize: 30, color: C.muted, marginTop: 12, opacity: appear(frame, 8) }}>
        Gemini Flash-Lite · 60 real forum questions, held out and run once with frozen settings
      </div>
      <div style={{ display: "flex", gap: 28, marginTop: 70 }}>
        {METRICS.map((m, i) => {
          const start = 20 + i * 10;
          const s = spring({ frame: frame - start, fps, config: { damping: 200 } });
          const v = interpolate(frame, [start, start + 40], [0, m.value], { ...clamp, easing: ease });
          return (
            <Panel
              key={m.label}
              style={{
                width: 380,
                padding: "34px 30px",
                textAlign: "center",
                opacity: s,
                transform: `translateY(${(1 - s) * 40}px)`,
              }}
            >
              <div style={{ fontSize: 92, fontWeight: 700, color: C.teal, fontFamily: SANS }}>
                {v.toFixed(m.decimals)}
                {m.suffix}
              </div>
              <div style={{ fontSize: 32, color: C.text, marginTop: 6 }}>{m.label}</div>
              <div style={{ fontSize: 22, color: C.muted, marginTop: 8 }}>{m.note}</div>
            </Panel>
          );
        })}
      </div>
      <div style={{ fontFamily: MONO, fontSize: 30, color: C.text, marginTop: 80, opacity: appear(frame, 90) }}>
        {REPO}
      </div>
    </AbsoluteFill>
  );
};

export const Demo: React.FC = () => (
  <AbsoluteFill>
    <Background />
    <Sequence from={SCENES.intro.from} durationInFrames={SCENES.intro.len}>
      <Fade len={SCENES.intro.len}>
        <Intro />
      </Fade>
    </Sequence>
    <Sequence from={SCENES.pipeline.from} durationInFrames={SCENES.pipeline.len}>
      <Fade len={SCENES.pipeline.len}>
        <Pipeline />
      </Fade>
    </Sequence>
    <Sequence from={SCENES.answered.from} durationInFrames={SCENES.answered.len}>
      <Fade len={SCENES.answered.len}>
        <Answered />
      </Fade>
    </Sequence>
    <Sequence from={SCENES.refused.from} durationInFrames={SCENES.refused.len}>
      <Fade len={SCENES.refused.len}>
        <Refused />
      </Fade>
    </Sequence>
    <Sequence from={SCENES.metrics.from} durationInFrames={SCENES.metrics.len}>
      <Fade len={SCENES.metrics.len}>
        <Metrics />
      </Fade>
    </Sequence>
  </AbsoluteFill>
);
