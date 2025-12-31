/**
 * Hyperparameter Editor Component
 * Provides UI controls for editing API hyperparameters
 */

import { Card } from '../../../../components/ui/Card';
import { Cpu } from 'lucide-react';
import type { HyperParams, APIConfig } from '../hooks/useAPIDetail';
import type { HyperparamDefinitionItem } from '../config/hyperparamDefinitions';

interface HyperparamEditorProps {
  hyperparamDefs: HyperparamDefinitionItem[];
  config: APIConfig;
  setConfig: React.Dispatch<React.SetStateAction<APIConfig>>;
}

export function HyperparamEditor({
  hyperparamDefs,
  config,
  setConfig,
}: HyperparamEditorProps) {
  if (hyperparamDefs.length === 0) {
    return null;
  }

  const updateHyperparam = (paramKey: string, value: number | boolean | string) => {
    const newHyperparams: HyperParams = { ...config.hyperparams };
    newHyperparams[paramKey] = value;
    setConfig({ ...config, hyperparams: newHyperparams });
  };

  return (
    <Card className="md:col-span-2">
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Cpu className="h-5 w-5" />
          하이퍼파라미터
        </h3>

        <div className="grid md:grid-cols-3 gap-4">
          {hyperparamDefs.map((param, idx) => {
            // Use param.key if available (dynamic), otherwise fallback to index-based key
            const paramKey = param.key || Object.keys(config.hyperparams)[idx] || `param_${idx}`;
            const value = param.key
              ? config.hyperparams[paramKey]
              : Object.values(config.hyperparams)[idx];

            return (
              <div key={paramKey}>
                <label className="block text-sm font-medium mb-1" title={param.description}>
                  {param.label}
                </label>
                {param.type === 'boolean' ? (
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={value as boolean}
                      onChange={(e) => updateHyperparam(paramKey, e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-muted-foreground">{param.description}</span>
                  </label>
                ) : param.type === 'select' ? (
                  <select
                    value={value as string}
                    onChange={(e) => updateHyperparam(paramKey, e.target.value)}
                    className="w-full px-3 py-2 border rounded bg-background"
                  >
                    {param.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={param.type}
                    value={value as string | number}
                    min={param.min}
                    max={param.max}
                    step={param.step}
                    onChange={(e) => {
                      const newValue = param.type === 'number'
                        ? parseFloat(e.target.value)
                        : e.target.value;
                      updateHyperparam(paramKey, newValue);
                    }}
                    className="w-full px-3 py-2 border rounded bg-background"
                  />
                )}
                <p className="text-xs text-muted-foreground mt-1">{param.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
