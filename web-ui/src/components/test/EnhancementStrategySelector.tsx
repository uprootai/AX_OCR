/**
 * Enhancement Strategy Selector Component
 *
 * Allows users to select OCR enhancement strategies:
 * - Basic: Original eDOCr (baseline)
 * - EDGNet: EDGNet preprocessing for improved GD&T detection
 * - VL: Vision-Language model for advanced recognition
 * - Hybrid: Combine EDGNet + VL for best quality
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Info, Zap, Brain, Layers } from 'lucide-react';

export type EnhancementStrategy = 'basic' | 'edgnet' | 'vl' | 'hybrid';

export interface StrategyInfo {
  id: EnhancementStrategy;
  name: string;
  description: string;
  icon: typeof Info;
  performance: {
    dimension: string;
    gdt: string;
  };
  processingTime: string;
  features: string[];
  badgeColor: 'default' | 'secondary' | 'success' | 'warning';
  recommended?: boolean;
}

const STRATEGIES: StrategyInfo[] = [
  {
    id: 'basic',
    name: 'Basic (Original)',
    description: 'Original eDOCr engine - Fastest processing',
    icon: Zap,
    performance: {
      dimension: '~50%',
      gdt: '0%',
    },
    processingTime: '~30-40초',
    features: ['CRAFT detector', 'CRNN recognizer', 'Basic box detection'],
    badgeColor: 'default',
  },
  {
    id: 'edgnet',
    name: 'EDGNet Enhanced',
    description: 'Uses EDGNet segmentation to improve GD&T detection',
    icon: Layers,
    performance: {
      dimension: '~60%',
      gdt: '50-60%',
    },
    processingTime: '~45-55초',
    features: ['Graph neural network', 'Smart region detection', 'Improved GD&T recall'],
    badgeColor: 'secondary',
    recommended: true,
  },
  {
    id: 'vl',
    name: 'VL-Powered',
    description: 'Vision-Language model for advanced recognition',
    icon: Brain,
    performance: {
      dimension: '~85%',
      gdt: '70-75%',
    },
    processingTime: '~50-70초',
    features: ['GPT-4V / Claude 3', 'Context understanding', 'High accuracy'],
    badgeColor: 'success',
  },
  {
    id: 'hybrid',
    name: 'Hybrid (Best Quality)',
    description: 'Combines EDGNet + VL for maximum accuracy',
    icon: Brain,
    performance: {
      dimension: '~90%',
      gdt: '80-85%',
    },
    processingTime: '~60-80초',
    features: ['EDGNet + VL ensemble', 'Deduplication', 'Production quality'],
    badgeColor: 'warning',
  },
];

interface EnhancementStrategySelectorProps {
  value: EnhancementStrategy;
  onChange: (strategy: EnhancementStrategy) => void;
  disabled?: boolean;
}

export default function EnhancementStrategySelector({
  value,
  onChange,
  disabled = false,
}: EnhancementStrategySelectorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          성능 개선 전략 선택
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-2">
          OCR 성능을 개선하는 다양한 전략을 선택할 수 있습니다. 기존 기능은 Basic으로, 성능 개선 옵션은 추가 기능으로 제공됩니다.
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3">
          {STRATEGIES.map((strategy) => {
            const isSelected = value === strategy.id;
            const Icon = strategy.icon;

            return (
              <button
                key={strategy.id}
                onClick={() => onChange(strategy.id)}
                disabled={disabled}
                className={`
                  relative p-4 rounded-lg border-2 transition-all text-left
                  ${isSelected
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50 hover:bg-accent/50'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                {/* Recommended Badge */}
                {strategy.recommended && (
                  <div className="absolute -top-2 -right-2">
                    <Badge variant="success" className="text-xs">
                      추천
                    </Badge>
                  </div>
                )}

                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div className={`
                    p-2 rounded-lg
                    ${isSelected ? 'bg-primary/10' : 'bg-muted'}
                  `}>
                    <Icon className={`h-5 w-5 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Title and Badge */}
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className={`font-semibold ${isSelected ? 'text-primary' : ''}`}>
                        {strategy.name}
                      </h3>
                      <Badge variant={strategy.badgeColor} className="text-xs">
                        {strategy.performance.gdt} GD&T
                      </Badge>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-muted-foreground mb-2">
                      {strategy.description}
                    </p>

                    {/* Performance Stats */}
                    <div className="flex gap-4 text-xs mb-2">
                      <div>
                        <span className="text-muted-foreground">치수: </span>
                        <span className="font-medium">{strategy.performance.dimension}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">GD&T: </span>
                        <span className="font-medium">{strategy.performance.gdt}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">처리시간: </span>
                        <span className="font-medium">{strategy.processingTime}</span>
                      </div>
                    </div>

                    {/* Features */}
                    <div className="flex flex-wrap gap-1">
                      {strategy.features.map((feature, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Radio indicator */}
                  <div className={`
                    w-5 h-5 rounded-full border-2 flex items-center justify-center
                    ${isSelected ? 'border-primary' : 'border-border'}
                  `}>
                    {isSelected && (
                      <div className="w-3 h-3 rounded-full bg-primary" />
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* VL Provider Selection (only for VL/Hybrid) */}
        {(value === 'vl' || value === 'hybrid') && (
          <div className="mt-4 p-3 rounded-lg bg-muted">
            <label className="text-sm font-medium mb-2 block">
              VL Model Provider
            </label>
            <select className="w-full px-3 py-2 rounded-md border border-border bg-background">
              <option value="openai">OpenAI GPT-4V (기본값)</option>
              <option value="anthropic">Anthropic Claude 3</option>
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              * API 키 설정 필요 (환경변수: OPENAI_API_KEY or ANTHROPIC_API_KEY)
            </p>
          </div>
        )}

        {/* Info Panel */}
        <div className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <div className="flex gap-2">
            <Info className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-700 dark:text-blue-300">
              <p className="font-medium mb-1">성능 개선 원리</p>
              <ul className="space-y-1 list-disc list-inside">
                <li><strong>EDGNet</strong>: GraphSAGE로 GD&T 후보 영역 사전 탐지</li>
                <li><strong>VL</strong>: GPT-4V/Claude 3로 컨텍스트 이해 기반 인식</li>
                <li><strong>Hybrid</strong>: 두 방식을 앙상블하여 최고 정확도 달성</li>
              </ul>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
