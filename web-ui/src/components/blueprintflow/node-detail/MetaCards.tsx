import { Info, ArrowRight, Lightbulb, Link, ChevronDown, ChevronUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import type { NodeDefinition } from '../../../config/nodes/types';

interface DescriptionCardProps {
  definition: NodeDefinition;
}

export function DescriptionCard({ definition }: DescriptionCardProps) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Info className="w-4 h-4" />
          {t('nodeDetail.description')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-700 dark:text-gray-300">{definition.description}</p>
      </CardContent>
    </Card>
  );
}

interface IOCardsProps {
  definition: NodeDefinition;
}

export function NodeIOCards({ definition }: IOCardsProps) {
  const { t } = useTranslation();
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <ArrowRight className="w-4 h-4 rotate-180 text-blue-500" />
            {t('nodeDetail.inputs')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {definition.inputs.map((input, idx) => (
            <div key={idx} className="border-l-2 border-blue-500 pl-3 py-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400">
                  {input.name}
                </span>
                <span className="text-xs text-gray-500">: {input.type}</span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{input.description}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-green-500" />
            {t('nodeDetail.outputs')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {definition.outputs.map((output, idx) => (
            <div key={idx} className="border-l-2 border-green-500 pl-3 py-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-semibold text-green-600 dark:text-green-400">
                  {output.name}
                </span>
                <span className="text-xs text-gray-500">: {output.type}</span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{output.description}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </>
  );
}

interface ExamplesCardProps {
  definition: NodeDefinition;
  showExamples: boolean;
  onToggle: () => void;
}

export function ExamplesCard({ definition, showExamples, onToggle }: ExamplesCardProps) {
  const { t } = useTranslation();
  if (definition.examples.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-between cursor-pointer"
        >
          <CardTitle className="text-sm">💡 {t('nodeDetail.usageExample')}</CardTitle>
          {showExamples ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </CardHeader>
      {showExamples && (
        <CardContent>
          <ul className="space-y-2">
            {definition.examples.map((example, idx) => (
              <li key={idx} className="text-xs text-gray-600 dark:text-gray-400 flex gap-2">
                <span className="text-gray-400">•</span>
                <span>{example}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      )}
    </Card>
  );
}

interface UsageTipsCardProps {
  definition: NodeDefinition;
}

export function UsageTipsCard({ definition }: UsageTipsCardProps) {
  const { t } = useTranslation();
  if (!definition.usageTips || definition.usageTips.length === 0) return null;

  return (
    <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2 text-blue-900 dark:text-blue-300">
          <Lightbulb className="w-4 h-4" />
          💡 {t('nodeDetail.usageTip')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2.5">
          {definition.usageTips.map((tip, idx) => (
            <li key={idx} className="text-xs text-blue-800 dark:text-blue-200 flex gap-2 leading-relaxed">
              <span className="text-blue-400 mt-0.5">•</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

interface RecommendedInputsCardProps {
  definition: NodeDefinition;
}

export function RecommendedInputsCard({ definition }: RecommendedInputsCardProps) {
  const { t } = useTranslation();
  if (!definition.recommendedInputs || definition.recommendedInputs.length === 0) return null;

  return (
    <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800">
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2 text-green-900 dark:text-green-300">
          <Link className="w-4 h-4" />
          🔗 {t('nodeDetail.recommendedConnections')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {definition.recommendedInputs.map((rec, idx) => (
            <div key={idx} className="border-l-2 border-green-500 pl-3 py-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs font-semibold text-green-700 dark:text-green-400">
                  {rec.from}
                </span>
                <ArrowRight className="w-3 h-3 text-green-600" />
                <span className="font-mono text-xs text-green-600 dark:text-green-400">
                  {rec.field}
                </span>
              </div>
              <p className="text-xs text-green-800 dark:text-green-200 leading-relaxed">{rec.reason}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
