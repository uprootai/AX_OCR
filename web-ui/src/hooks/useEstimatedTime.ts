import { useEffect, useState } from 'react';

interface UseEstimatedTimeOptions {
  totalSteps: number;
  completedSteps: number;
  startTime: number;
  isComplete: boolean;
}

export function useEstimatedTime({
  totalSteps,
  completedSteps,
  startTime,
  isComplete
}: UseEstimatedTimeOptions) {
  const [estimatedTime, setEstimatedTime] = useState<string>('계산 중...');
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);

  useEffect(() => {
    if (isComplete) {
      setEstimatedTime('완료');
      setRemainingSeconds(0);
      return;
    }

    if (completedSteps === 0) {
      setEstimatedTime('계산 중...');
      setRemainingSeconds(0);
      return;
    }

    const elapsed = (Date.now() - startTime) / 1000; // seconds
    const avgTimePerStep = elapsed / completedSteps;
    const remainingSteps = totalSteps - completedSteps;
    const estimated = avgTimePerStep * remainingSteps;

    setRemainingSeconds(Math.ceil(estimated));

    if (estimated < 1) {
      setEstimatedTime('곧 완료');
    } else if (estimated < 60) {
      setEstimatedTime(`약 ${Math.ceil(estimated)}초 남음`);
    } else {
      const minutes = Math.ceil(estimated / 60);
      setEstimatedTime(`약 ${minutes}분 남음`);
    }
  }, [completedSteps, totalSteps, startTime, isComplete]);

  return { estimatedTime, remainingSeconds };
}
