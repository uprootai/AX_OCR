/**
 * Docker Control Card Component
 * Provides start/stop/restart controls for Docker containers
 */

import { Card } from '../../../../components/ui/Card';
import { Button } from '../../../../components/ui/Button';
import {
  Play,
  Square,
  RefreshCw,
  HardDrive,
} from 'lucide-react';

interface DockerControlCardProps {
  apiId: string;
  dockerAction: string | null;
  onDockerAction: (action: 'start' | 'stop' | 'restart') => Promise<void>;
}

export function DockerControlCard({
  apiId,
  dockerAction,
  onDockerAction,
}: DockerControlCardProps) {
  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <HardDrive className="h-5 w-5" />
          Docker 제어
        </h3>

        <div className="space-y-4">
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onDockerAction('start')}
              disabled={dockerAction !== null}
            >
              <Play className="h-4 w-4 mr-2" />
              {dockerAction === 'start' ? '시작 중...' : '시작'}
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onDockerAction('stop')}
              disabled={dockerAction !== null}
            >
              <Square className="h-4 w-4 mr-2" />
              {dockerAction === 'stop' ? '중지 중...' : '중지'}
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onDockerAction('restart')}
              disabled={dockerAction !== null}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {dockerAction === 'restart' ? '재시작 중...' : '재시작'}
            </Button>
          </div>

          <div className="p-3 bg-muted/50 rounded text-sm">
            <p className="text-muted-foreground">
              컨테이너: <code className="bg-muted px-1 rounded">{apiId}-api</code>
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
