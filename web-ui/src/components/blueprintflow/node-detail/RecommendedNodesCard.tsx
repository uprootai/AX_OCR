import { Lightbulb, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { useNodeDefinitions } from '../../../hooks/useNodeDefinitions';

interface RecommendedNodesCardProps {
  nodes: string[];
  descriptions: string[];
  onAddNode?: (nodeType: string) => void;
}

export function RecommendedNodesCard({ nodes, descriptions, onAddNode }: RecommendedNodesCardProps) {
  const { getDefinition } = useNodeDefinitions();

  return (
    <Card className="border-orange-200 dark:border-orange-800 bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20">
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2 text-orange-700 dark:text-orange-300">
          <Lightbulb className="w-4 h-4" />
          📌 추천 노드
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1">
          {descriptions.map((desc, idx) => (
            <p key={idx} className="text-xs text-orange-800 dark:text-orange-200">
              • {desc}
            </p>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          {nodes.map((nodeTypeId) => {
            const nodeDef = getDefinition(nodeTypeId);
            return (
              <button
                key={nodeTypeId}
                onClick={() => onAddNode?.(nodeTypeId)}
                disabled={!onAddNode}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-white dark:bg-gray-700 border border-orange-300 dark:border-orange-600 text-orange-700 dark:text-orange-300 hover:bg-orange-100 dark:hover:bg-orange-800/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                <Plus className="w-3 h-3" />
                {nodeDef?.label || nodeTypeId}
              </button>
            );
          })}
        </div>

        <div className="flex items-start gap-2 p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
          <span className="text-orange-500">💡</span>
          <span className="text-xs text-orange-800 dark:text-orange-200">
            선택한 기능에 필요한 노드입니다. 클릭하여 추가하세요.
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
