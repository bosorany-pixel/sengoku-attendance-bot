import { useMemo } from 'react';

const SPARK_COUNT = 24;

/** Deterministic "random" for consistent sparks across renders */
function seeded(i: number) {
  const x = Math.sin(i * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

export function SparkBackground() {
  const sparks = useMemo(() => {
    return Array.from({ length: SPARK_COUNT }, (_, i) => ({
      left: `${seeded(i) * 100}%`,
      delay: `${seeded(i + 1) * 4}s`,
      duration: 2.5 + seeded(i + 2) * 2,
      size: 2 + Math.floor(seeded(i + 3) * 3),
      opacity: 0.7 + seeded(i + 4) * 0.4,
    }));
  }, []);

  return (
    <div
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
      aria-hidden
    >
      {sparks.map((s, i) => (
        <div
          key={i}
          className="spark"
          style={{
            left: s.left,
            animationDelay: s.delay,
            animationDuration: `${s.duration}s`,
            width: s.size,
            height: s.size,
            ['--spark-opacity' as string]: s.opacity,
          }}
        />
      ))}
    </div>
  );
}
