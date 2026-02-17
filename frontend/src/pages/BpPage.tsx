import { useParams } from 'react-router-dom';
import { useLevelsAndAchievements } from '../hooks/useLevels';
import { useUserAchievements } from '../hooks/useUserAchievements';
import { useMembers } from '../hooks/useMembers';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Achievement } from '../lib/types';
import { motion } from 'framer-motion';
import { useMemo } from 'react';

/** Map level number -> achievement description (first achievement for that level, if any) */
function levelToDescription(achievements: Achievement[]): Record<number, string> {
  const map: Record<number, string> = {};
  for (const a of achievements) {
    if (map[a.bp_level] == null) map[a.bp_level] = a.description || '—';
  }
  return map;
}

export function BpPage() {
  const { uid } = useParams<{ uid: string }>();
  const userId = uid ?? '';

  const { data: levelsData, isLoading: levelsLoading, error: levelsError } = useLevelsAndAchievements();
  const { data: userData, isLoading: userLoading, error: userError } = useUserAchievements(userId);
  const { data: members } = useMembers();

  const user = members?.find((m) => m.uid === userId);
  const eventCount = user?.event_count ?? 0;
  const displayName = userData?.user?.display_name ?? user?.display_name ?? '—';

  const { pointsToNextLevel, levelsWithProgress } = useMemo(() => {
    const levels = levelsData?.levels ?? [];
    const achievements = levelsData?.achievements ?? [];
    const descMap = levelToDescription(achievements);

    const sortedLevels = [...levels].sort((a, b) => a.level - b.level);
    const nextLevel = sortedLevels.find((l) => l.attendance > eventCount);
    const pointsToNextLevel = nextLevel != null ? nextLevel.attendance - eventCount : null;

    const firstUnachievedIndex = sortedLevels.findIndex((l) => l.attendance > eventCount);
    const withProgress = sortedLevels.map((l, index) => {
      const required = l.attendance;
      const current = Math.min(eventCount, required);
      const achieved = eventCount >= required;
      const isNextLevel = index === firstUnachievedIndex;
      return {
        level: l.level,
        current,
        total: required,
        achieved,
        isNextLevel,
        description: descMap[l.level] ?? '—',
      };
    });

    return { pointsToNextLevel, levelsWithProgress: withProgress };
  }, [levelsData, eventCount]);

  const error = levelsError ?? userError;
  const isLoading = levelsLoading || (userId && userLoading);

  if (error) {
    return (
      <Layout title="Ошибка" subtitle="Не удалось загрузить данные">
        <div className="text-red-400">
          {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </Layout>
    );
  }

  if (isLoading || !levelsData) {
    return (
      <Layout title="Батлпас" subtitle="Загрузка...">
        <LoadingSpinner />
      </Layout>
    );
  }

  const subtitle = userId ? `Батлпас · ${displayName}` : 'Батлпас';

  return (
    <Layout title="Батлпас" subtitle={subtitle}>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="max-w-2xl mx-auto flex flex-col items-center text-center w-full"
      >
        {userId && (
          <div className="mb-8 space-y-2 flex flex-col items-center">
            <div>
              <span className="text-dark-textLight text-sm">ник: </span>
              <span className="inline-block px-2 py-0.5 border border-dark-border rounded text-white font-medium">
                {displayName}
              </span>
            </div>
            <div className="text-dark-textLight text-sm">
              очков до следующего левела:
              <div className="text-white font-semibold mt-0.5">
                {pointsToNextLevel !== null ? pointsToNextLevel : '—'}
              </div>
            </div>
          </div>
        )}

        {levelsWithProgress.length === 0 ? (
          <p className="text-dark-textLight">Нет уровней</p>
        ) : (
          <div className="relative pl-0 w-full max-w-md mx-auto">
            {/* One continuous vertical line: grey by default, bright white for achieved segments. Grey/white dots. */}
            <div
              className="absolute flex flex-col items-center top-0 bottom-0"
              style={{ left: '5.25rem' }}
              aria-hidden
            >
              {levelsWithProgress.map((item, index) => {
                const segAboveWhite = index > 0 && levelsWithProgress[index - 1].achieved;
                const dotWhite = item.achieved;
                const segBelowWhite = item.achieved;
                const showParticles = dotWhite || item.isNextLevel;
                const particleClass = dotWhite && !item.isNextLevel
                  ? 'bp-particle-steady'
                  : item.isNextLevel
                    ? 'bp-particle-pulse'
                    : '';
                const dotExtraClass = dotWhite
                  ? 'bg-white border-white bp-dot-glow'
                  : item.isNextLevel
                    ? 'bg-dark-border border-dark-border bp-dot-next-pulse'
                    : 'bg-dark-border border-dark-border';
                return (
                  <div
                    key={item.level}
                    className="flex flex-col items-center flex-shrink-0 w-0 h-14"
                  >
                    <div
                      className={`w-0.5 flex-1 min-h-[0.5rem] ${segAboveWhite ? 'bg-white' : 'bg-dark-border'}`}
                    />
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
                              <div
                                key={deg}
                                className={`${particleClass} absolute w-1 h-1 rounded-full bg-white pointer-events-none`}
                                style={{ left: x, top: y }}
                              />
                            );
                          })}
                        </>
                      )}
                      <div
                        className={`flex-shrink-0 w-3.5 h-3.5 rounded-full border-2 relative z-10 ${dotExtraClass}`}
                      />
                    </div>
                    <div
                      className={`w-0.5 flex-1 min-h-[0.5rem] ${segBelowWhite ? 'bg-white' : 'bg-dark-border'}`}
                    />
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
                  className="flex items-center gap-3 h-14 py-0"
                >
                  <div className="w-16 flex-shrink-0 text-right">
                    <span className="text-dark-textLight text-sm tabular-nums">
                      {item.current}/{item.total}
                    </span>
                  </div>
                  <div className="w-6 flex-shrink-0" aria-hidden />
                  <div className="flex-1 min-w-0 flex items-center leading-tight">
                    <span className="text-dark-textLight text-xs mr-2">{item.level}</span>
                    <span className={`text-[0.95rem] ${item.achieved ? 'text-white' : 'text-dark-textLight'}`}>
                      {item.description}
                    </span>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>
        )}
      </motion.div>
    </Layout>
  );
}
