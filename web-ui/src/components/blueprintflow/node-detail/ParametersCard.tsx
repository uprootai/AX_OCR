import { Settings, ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  getGroupImplementationStats,
  formatImplementationCount,
  getImplementationStatusIcon,
  type FeatureGroup,
} from '../../../config/features';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { ProfileManager } from '../ProfileManager';
import type { ProfileParams } from '../../../store/profileStore';
import type { Node } from 'reactflow';
import type { NodeDefinition, CheckboxOption } from '../../../config/nodes/types';
import { isSelectOption, isCheckboxOption } from './types';

interface ParametersCardProps {
  definition: NodeDefinition;
  selectedNode: Node;
  nodeType: string;
  showParameters: boolean;
  onToggle: () => void;
  onUpdateNode: (nodeId: string, data: Record<string, unknown>) => void;
}

export function ParametersCard({
  definition,
  selectedNode,
  nodeType,
  showParameters,
  onToggle,
  onUpdateNode,
}: ParametersCardProps) {
  const { t } = useTranslation();

  const handleParameterChange = (paramName: string, value: string | number | boolean | string[]) => {
    const currentData = selectedNode.data || {};
    const currentParams = currentData.parameters || {};
    onUpdateNode(selectedNode.id, {
      ...currentData,
      parameters: {
        ...currentParams,
        [paramName]: value,
      },
    });
  };

  const handleCheckboxToggle = (paramName: string, optionValue: string, currentValues: string[]) => {
    const newValues = currentValues.includes(optionValue)
      ? currentValues.filter((v) => v !== optionValue)
      : [...currentValues, optionValue];
    handleParameterChange(paramName, newValues);
  };

  const renderCheckboxOption = (
    opt: CheckboxOption,
    currentValue: unknown,
    paramName: string
  ) => {
    if (!isCheckboxOption(opt)) return null;
    const isChecked = Array.isArray(currentValue) ? currentValue.includes(opt.value) : false;

    const implStatus = opt.implementationStatus;
    const statusIcon = implStatus ? getImplementationStatusIcon(implStatus) : '';
    const statusLabel =
      implStatus === 'implemented' ? '완전 구현'
      : implStatus === 'partial' ? '부분 구현'
      : implStatus === 'stub' ? '스텁만'
      : implStatus === 'planned' ? '계획됨' : '';

    return (
      <div key={opt.value} className="group relative">
        <label
          className={`flex items-center gap-2 p-1.5 rounded cursor-pointer transition-colors ${
            isChecked
              ? 'bg-blue-100 dark:bg-blue-900/40 border border-blue-300 dark:border-blue-600'
              : 'hover:bg-gray-100 dark:hover:bg-gray-600/50'
          }`}
        >
          <input
            type="checkbox"
            checked={isChecked}
            onChange={() =>
              handleCheckboxToggle(
                paramName,
                opt.value,
                Array.isArray(currentValue) ? currentValue : []
              )
            }
            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm flex items-center gap-1">
            {opt.icon && <span>{opt.icon}</span>}
            {opt.label}
            {statusIcon && (
              <span title={statusLabel} className="text-xs opacity-70">
                {statusIcon}
              </span>
            )}
          </span>
          {opt.hint && (
            <span className="text-xs text-gray-400 ml-auto">{opt.hint}</span>
          )}
        </label>
        {opt.description && (
          <div className="absolute z-50 hidden group-hover:block w-72 p-3 text-xs bg-gray-900 text-white rounded-lg shadow-xl left-0 top-full mt-1 leading-relaxed">
            <div className="flex items-start gap-2">
              <span className="text-lg flex-shrink-0">{opt.icon}</span>
              <div>
                <div className="font-semibold text-blue-300 mb-1 flex items-center gap-2">
                  {opt.label}
                  {statusIcon && (
                    <span className="text-xs bg-gray-700 px-1.5 py-0.5 rounded">
                      {statusIcon} {statusLabel}
                    </span>
                  )}
                </div>
                <div className="text-gray-200">{opt.description}</div>
                {opt.implementationLocation && (
                  <div className="text-gray-400 mt-1 text-[10px]">
                    📁 {opt.implementationLocation}
                  </div>
                )}
              </div>
            </div>
            <div className="absolute -top-1.5 left-4 w-3 h-3 bg-gray-900 rotate-45"></div>
          </div>
        )}
      </div>
    );
  };

  const renderCheckboxGroup = (
    paramName: string,
    options: typeof definition.parameters[0]['options'],
    currentValue: unknown
  ) => {
    const groupedOptions: Record<string, CheckboxOption[]> = {};
    const ungroupedOptions: CheckboxOption[] = [];

    options?.forEach((opt) => {
      if (!isCheckboxOption(opt)) return;
      const cbOpt = opt as CheckboxOption;
      if (cbOpt.group) {
        if (!groupedOptions[cbOpt.group]) groupedOptions[cbOpt.group] = [];
        groupedOptions[cbOpt.group]!.push(cbOpt);
      } else {
        ungroupedOptions.push(cbOpt);
      }
    });

    const groups = Object.keys(groupedOptions);
    const hasGroups = groups.length > 0;

    const groupIcons: Record<string, string> = {
      '기본 검출': '🎯',
      'GD&T / 기계': '🔧',
      'P&ID': '🔀',
      'BOM 생성': '📋',
      '장기 로드맵': '🚀',
    };

    const groupColors: Record<string, string> = {
      '기본 검출': 'border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-900/20',
      'GD&T / 기계': 'border-orange-300 dark:border-orange-700 bg-orange-50/50 dark:bg-orange-900/20',
      'P&ID': 'border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-900/20',
      'BOM 생성': 'border-purple-300 dark:border-purple-700 bg-purple-50/50 dark:bg-purple-900/20',
      '장기 로드맵': 'border-pink-300 dark:border-pink-700 bg-pink-50/50 dark:bg-pink-900/20',
    };

    return (
      <div className="space-y-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
        {hasGroups && groups.map((group) => {
          const opts = groupedOptions[group] || [];
          const stats = getGroupImplementationStats(group as FeatureGroup);
          const implCount = formatImplementationCount(stats);

          return (
            <div
              key={group}
              className={`rounded-lg border p-2 ${groupColors[group] || 'border-gray-200 dark:border-gray-600'}`}
            >
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-gray-200 dark:border-gray-600">
                <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                  {groupIcons[group] || '📁'} {group}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400" title="구현됨/전체">
                  {implCount} 구현
                </span>
              </div>
              <div className="space-y-1">
                {opts.map((opt) => renderCheckboxOption(opt, currentValue, paramName))}
              </div>
            </div>
          );
        })}

        {ungroupedOptions.length > 0 && (
          <div className="space-y-1">
            {ungroupedOptions.map((opt) => renderCheckboxOption(opt, currentValue, paramName))}
          </div>
        )}

        <div className="text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600 flex items-center justify-between">
          <span>{Array.isArray(currentValue) ? currentValue.length : 0}개 기능 활성화</span>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => {
                const allValues = options
                  ?.filter(isCheckboxOption)
                  .map((opt) => opt.value) || [];
                handleParameterChange(paramName, allValues);
              }}
              className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800/50"
            >
              전체 선택
            </button>
            <button
              type="button"
              onClick={() => handleParameterChange(paramName, [])}
              className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-500"
            >
              전체 해제
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-between cursor-pointer"
        >
          <CardTitle className="text-sm flex items-center gap-2">
            <Settings className="w-4 h-4 text-purple-500" />
            {t('nodeDetail.parameters')}
          </CardTitle>
          {showParameters ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </CardHeader>
      {showParameters && (
        <CardContent className="space-y-3">
          {definition.profiles && definition.profiles.available.length > 0 && (
            <ProfileManager
              nodeType={nodeType}
              definition={definition}
              currentParams={selectedNode.data?.parameters || {}}
              selectedProfile={selectedNode.data?.parameters?._profile}
              onProfileSelect={(profileName: string, params: ProfileParams) => {
                const currentData = selectedNode.data || {};
                const currentParams = currentData.parameters || {};
                onUpdateNode(selectedNode.id, {
                  ...currentData,
                  parameters: {
                    ...currentParams,
                    ...params,
                    _profile: profileName,
                  },
                });
              }}
              onParamsChange={(params) => {
                const currentData = selectedNode.data || {};
                onUpdateNode(selectedNode.id, {
                  ...currentData,
                  parameters: params,
                });
              }}
            />
          )}

          {definition.parameters.map((param) => {
            const currentValue =
              selectedNode.data?.parameters?.[param.name] ?? param.default;

            return (
              <div key={param.name} className="space-y-1">
                <label className="text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                  {param.name}
                  {param.tooltip && (
                    <span className="group relative">
                      <HelpCircle className="w-3 h-3 text-gray-400 hover:text-blue-500 cursor-help" />
                      <span className="absolute z-50 hidden group-hover:block w-64 p-2 text-xs bg-gray-900 text-white rounded-lg shadow-lg -left-28 top-5">
                        {param.tooltip}
                      </span>
                    </span>
                  )}
                </label>
                <p className="text-xs text-gray-500">{param.description}</p>

                {param.type === 'number' && (
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={param.min}
                      max={param.max}
                      step={param.step}
                      value={currentValue as number}
                      onChange={(e) =>
                        handleParameterChange(param.name, parseFloat(e.target.value))
                      }
                      className="flex-1"
                    />
                    <span className="text-xs font-mono w-12 text-right">{currentValue as number}</span>
                  </div>
                )}

                {(param.type === 'string' || param.type === 'textarea') && (
                  <textarea
                    value={(currentValue as string) || ''}
                    onChange={(e) => handleParameterChange(param.name, e.target.value)}
                    onFocus={(e) => e.stopPropagation()}
                    onKeyDown={(e) => e.stopPropagation()}
                    onMouseDown={(e) => e.stopPropagation()}
                    placeholder={param.placeholder || t('nodeDetail.enterText')}
                    rows={param.type === 'textarea' ? 4 : 3}
                    className="w-full px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white resize-y min-h-[60px] nodrag nopan font-mono"
                  />
                )}

                {param.type === 'select' && (
                  <div className="space-y-2">
                    <select
                      value={currentValue as string}
                      onChange={(e) => handleParameterChange(param.name, e.target.value)}
                      className="w-full px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600"
                    >
                      {param.options?.map((opt) => {
                        const value = isSelectOption(opt) ? opt.value : opt;
                        const label = isSelectOption(opt) ? opt.label : opt;
                        return (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        );
                      })}
                    </select>
                    {param.options?.some(isSelectOption) && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-2 rounded border border-gray-200 dark:border-gray-600">
                        {(() => {
                          const selectedOpt = param.options?.find(
                            (opt) => isSelectOption(opt) && opt.value === currentValue
                          );
                          if (selectedOpt && isSelectOption(selectedOpt)) {
                            return (
                              <div className="flex items-start gap-2">
                                <HelpCircle className="w-3 h-3 mt-0.5 text-blue-500 flex-shrink-0" />
                                <span>{selectedOpt.description}</span>
                              </div>
                            );
                          }
                          return null;
                        })()}
                      </div>
                    )}
                  </div>
                )}

                {param.type === 'boolean' && (
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={currentValue as boolean}
                      onChange={(e) => handleParameterChange(param.name, e.target.checked)}
                    />
                    <span className="text-xs">{t('nodeDetail.enabled')}</span>
                  </label>
                )}

                {param.type === 'checkboxGroup' &&
                  renderCheckboxGroup(param.name, param.options, currentValue)}
              </div>
            );
          })}
        </CardContent>
      )}
    </Card>
  );
}
