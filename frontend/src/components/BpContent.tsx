import { useLevelsAndAchievements } from '../hooks/useLevels';
import { useUserAchievements } from '../hooks/useUserAchievements';
import { useMembers } from '../hooks/useMembers';
import { LoadingSpinner } from './LoadingSpinner';
import type { Achievement } from '../lib/types';
import { motion } from 'framer-motion';
import { useMemo, useState, useEffect } from 'react';

function levelToAchievement(achievements: Achievement[]): Record<number, { description: string; picture: string }> {
  const map: Record<number, { description: string; picture: string }> = {};
  for (const a of achievements) {
    if (map[a.bp_level] == null)
      map[a.bp_level] = { description: a.description || '—', picture: a.picture || '' };
  }
  return map;
}

const DEFAULT_ROW_HEIGHT_PX = 56; /* height when no picture */
const MAX_ROW_HEIGHT_PX = 420; /* cap image-based row height */

interface BpContentProps {
  userId: string;
}

export function BpContent({ userId }: BpContentProps) {
  const { data: levelsData, isLoading: levelsLoading, error: levelsError } = useLevelsAndAchievements();
  const { data: userData, isLoading: userLoading, error: userError } = useUserAchievements(userId);
  const { data: members } = useMembers();

  const user = members?.find((m) => m.uid === userId);
  const eventCount = user?.event_count ?? 0;
  const displayName = userData?.user?.display_name ?? user?.display_name ?? '—';

  const { pointsToNextLevel, levelsWithProgress } = useMemo(() => {
    const levels = levelsData?.levels ?? [];
    const achievements = levelsData?.achievements ?? [];
    const achievementMap = levelToAchievement(achievements);
    const sortedLevels = [...levels].sort((a, b) => a.level - b.level);
    const nextLevel = sortedLevels.find((l) => l.attendance > eventCount);
    const pointsToNextLevel = nextLevel != null ? Math.round(nextLevel.attendance - eventCount) : null;
    const firstUnachievedIndex = sortedLevels.findIndex((l) => l.attendance > eventCount);
    const withProgress = sortedLevels.map((l, index) => {
      const required = Math.round(l.attendance);
      const current = Math.round(Math.min(eventCount, required));
      const achieved = eventCount >= required;
      const isNextLevel = index === firstUnachievedIndex;
      const ach = achievementMap[l.level];
      return {
        level: l.level,
        current,
        total: required,
        achieved,
        isNextLevel,
        description: ach?.description ?? '—',
        picture: ach?.picture ?? '',
      };
    });
    return { pointsToNextLevel, levelsWithProgress: withProgress };
  }, [levelsData, eventCount]);

  const [rowHeights, setRowHeights] = useState<Record<number, number>>({});

  useEffect(() => {
    if (!levelsWithProgress.length) return;
    levelsWithProgress.forEach((item) => {
      if (!item.picture) return;
      const img = new Image();
      img.onload = () => {
        const h = Math.min(MAX_ROW_HEIGHT_PX, Math.max(DEFAULT_ROW_HEIGHT_PX, img.naturalHeight));
        setRowHeights((prev) => (prev[item.level] === h ? prev : { ...prev, [item.level]: h }));
      };
      img.src = item.picture;
    });
  }, [levelsWithProgress]);

  const getRowHeightPx = (level: number, hasPicture: boolean) =>
    hasPicture ? (rowHeights[level] ?? DEFAULT_ROW_HEIGHT_PX) : DEFAULT_ROW_HEIGHT_PX;

  const error = levelsError ?? userError;
  const isLoading = levelsLoading || (userId && userLoading);

  if (error) {
    return (
      <div className="text-red-400">
        {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }
  if (isLoading || !levelsData) {
    return <LoadingSpinner />;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="w-full flex flex-row gap-6 items-start px-2"
    >
      {userId && (
        <div className="w-1/4 flex-shrink-0 min-w-0">
          <div className="bg-dark-card/80 border border-dark-border rounded-xl px-5 py-4 shadow-sm flex flex-col gap-3 text-left">
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="text-dark-textLight text-xs uppercase tracking-wider">ник</span>
              <span className="px-3 py-1 rounded-lg bg-dark-bg border border-dark-border text-white font-medium text-sm">
                {displayName}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-dark-textLight text-xs uppercase tracking-wider">поинтов до следующего левела</span>
              <span className={`mt-1 text-lg font-semibold tabular-nums ${pointsToNextLevel !== null && pointsToNextLevel > 0 ? 'text-accent-green' : 'text-white'}`}>
                {pointsToNextLevel !== null ? pointsToNextLevel : '—'}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className={userId ? 'flex-1 min-w-0' : 'w-full'}>
        {levelsWithProgress.length === 0 ? (
          <p className="text-dark-textLight text-sm py-8">Нет уровней</p>
        ) : (
          <div className="w-full">
            <p className="text-dark-textLight text-xs uppercase tracking-wider mb-3 text-left">Уровни</p>
            <div className="relative bg-dark-card/40 border border-dark-border rounded-2xl py-6 px-6 shadow-inner">
            <div
              className="absolute flex flex-col items-center top-6 bottom-6 z-20"
              style={{ left: '7rem' }}
              aria-hidden
            >
              {levelsWithProgress.map((item, index) => {
                const segAboveWhite = index > 0 && levelsWithProgress[index - 1].achieved;
                const dotWhite = item.achieved;
                const segBelowWhite = item.achieved;
                const showParticles = dotWhite || item.isNextLevel;
                const particleClass = dotWhite && !item.isNextLevel ? 'bp-particle-steady' : item.isNextLevel ? 'bp-particle-pulse' : '';
                const dotExtraClass = dotWhite ? 'bg-white border-white bp-dot-glow' : item.isNextLevel ? 'bg-dark-border border-dark-border bp-dot-next-pulse' : 'bg-dark-border border-dark-border';
                const rowHeightPx = getRowHeightPx(item.level, !!item.picture);
                const isFirst = index === 0;
                const isLast = index === levelsWithProgress.length - 1;
                return (
                  <div key={item.level} className="flex flex-col items-center flex-shrink-0 w-0" style={{ height: `${rowHeightPx}px` }}>
                    <div className={`bp-line-segment w-0.5 ${isFirst ? 'flex-none h-0 min-h-0' : 'flex-1 min-h-[0.5rem]'} ${segAboveWhite ? 'bg-white' : 'bg-dark-border'}`} />
                    <div className="relative flex flex-shrink-0 items-center justify-center w-6 h-6">
                      {showParticles && particleClass && (
                        <>
                          {[0, 60, 120, 180, 240, 300].map((deg) => {
                            const r = 10;
                            const cx = 12;
                            const cy = 12;
                            const x = cx + r * Math.cos((deg * Math.PI) / 180) - 2;
                            const y = cy + r * Math.sin((deg * Math.PI) / 180) - 2;
                            return (
                              <div key={deg} className={`${particleClass} absolute w-1 h-1 rounded-full bg-white pointer-events-none`} style={{ left: x, top: y }} />
                            );
                          })}
                        </>
                      )}
                      {item.isNextLevel ? (
                        <motion.div
                          className={`flex-shrink-0 w-3.5 h-3.5 rounded-full border-2 relative z-10 ${dotExtraClass}`}
                          animate={{ scale: [1, 1.07, 1], opacity: [1, 0.92, 1] }}
                          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
                        />
                      ) : (
                        <div className={`flex-shrink-0 w-3.5 h-3.5 rounded-full border-2 relative z-10 ${dotExtraClass}`} />
                      )}
                    </div>
                    <div className={`bp-line-segment w-0.5 ${isLast ? 'flex-1 min-h-[0.5rem] opacity-0' : 'flex-1 min-h-[0.5rem]'} ${segBelowWhite ? 'bg-white' : 'bg-dark-border'}`} />
                  </div>
                );
              })}
            </div>
            <ul className="relative list-none w-full">
              {levelsWithProgress.map((item, index) => (
                <motion.li
                  key={item.level}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  style={{
                    minHeight: `${getRowHeightPx(item.level, !!item.picture)}px`,
                    height: `${getRowHeightPx(item.level, !!item.picture)}px`,
                  }}
                  className={`relative flex items-center gap-3 py-0 rounded-lg px-2 -mx-2 transition-colors overflow-hidden ${
                    item.isNextLevel ? 'bg-white/5' : 'hover:bg-white/[0.03]'
                  } ${!item.picture ? 'bg-dark-card/20' : ''}`}
                >
                  {item.picture && (
                    <>
                      <div
                        className="absolute inset-0 bg-cover bg-right bg-no-repeat"
                        style={{ backgroundImage: `url(${item.picture})` }}
                        aria-hidden
                      />
                      <div
                        className="absolute inset-0 pointer-events-none"
                        style={{
                          background: 'linear-gradient(to right, #1e1e1e 0%, rgba(30,30,30,0.97) 25%, rgba(30,30,30,0.6) 55%, transparent 100%)',
                        }}
                        aria-hidden
                      />
                    </>
                  )}
                  <div className="relative z-10 flex items-center gap-3 w-full min-w-0">
                    <div className="w-16 flex-shrink-0 text-right">
                      <span className="text-dark-textLight text-sm tabular-nums">
                        <span className={item.achieved ? 'text-white' : undefined}>{item.current}</span>
                        <span className="text-dark-border">/</span>
                        <span>{item.total}</span>
                      </span>
                    </div>
                    <div className="w-6 flex-shrink-0" aria-hidden />
                    <div className="flex-1 min-w-0 flex items-center leading-tight gap-2">
                      <span
                        className={`inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold min-w-[1.25rem] flex-shrink-0 ${
                          item.achieved ? 'bg-white/20 text-white' : item.isNextLevel ? 'bg-accent-green/20 text-accent-green' : 'bg-dark-border/60 text-dark-textLight'
                        }`}
                      >
                        {item.level}
                      </span>
                      <span className={`text-[0.95rem] ${item.achieved ? 'text-white' : item.isNextLevel ? 'text-accent-green/90' : 'text-dark-textLight'}`}>
                        {item.description}
                      </span>
                    </div>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>
        </div>
        )}
      </div>
    </motion.div>
  );
}
