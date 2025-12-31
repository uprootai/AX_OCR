/**
 * IndustryEquipmentSection - 산업 장비 태그 인식 섹션
 * P&ID 도면에서 장비 태그(ECU-001, FMU-002 등)를 인식하고 관리
 */

import { useState } from 'react';
import { Factory, Tag, Download, Search, ChevronDown, ChevronUp } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';

interface EquipmentTag {
  id: string;
  tag: string;                    // ECU-001, FMU-002 등
  type: string;                   // ECU, FMU, PUMP 등
  fullName?: string;              // Electrolyzer Cell Unit
  location?: { x: number; y: number; width: number; height: number };
  confidence: number;
  verified: boolean;
}

interface IndustryProfile {
  id: string;
  name: string;
  description: string;
  patterns: string[];
}

interface IndustryEquipmentSectionProps {
  sessionId: string;
  equipmentTags: EquipmentTag[];
  selectedProfile: IndustryProfile | null;
  availableProfiles: IndustryProfile[];
  onSelectProfile: (profileId: string) => void;
  onVerifyTag: (tagId: string, verified: boolean) => void;
  onExport: (format: 'excel' | 'csv' | 'json') => void;
  isLoading: boolean;
}

// 기본 프로파일 목록 (백엔드에서 로드하기 전 기본값)
const DEFAULT_PROFILES: IndustryProfile[] = [
  {
    id: 'bwms',
    name: 'BWMS (선박평형수)',
    description: 'ECU, FMU, ANU, TSU 등',
    patterns: ['ECU-*', 'FMU-*', 'ANU-*', 'TSU-*', 'APU-*'],
  },
  {
    id: 'process',
    name: '일반 공정',
    description: 'PUMP, VALVE, TANK 등',
    patterns: ['P-*', 'V-*', 'TK-*', 'HX-*'],
  },
  {
    id: 'power',
    name: '발전/전력',
    description: 'GEN, XFMR, CB 등',
    patterns: ['GEN-*', 'XFMR-*', 'CB-*', 'MCC-*'],
  },
];

export function IndustryEquipmentSection({
  sessionId,
  equipmentTags,
  selectedProfile,
  availableProfiles = DEFAULT_PROFILES,
  onSelectProfile,
  onVerifyTag,
  onExport,
  isLoading,
}: IndustryEquipmentSectionProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

  // 장비 타입별 그룹화
  const groupedByType = equipmentTags.reduce((acc, tag) => {
    if (!acc[tag.type]) {
      acc[tag.type] = [];
    }
    acc[tag.type].push(tag);
    return acc;
  }, {} as Record<string, EquipmentTag[]>);

  // 검색 필터링
  const filteredTags = searchQuery
    ? equipmentTags.filter(
        (tag) =>
          tag.tag.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tag.type.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : equipmentTags;

  const toggleType = (type: string) => {
    const newSet = new Set(expandedTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setExpandedTypes(newSet);
  };

  const verifiedCount = equipmentTags.filter((t) => t.verified).length;
  const totalCount = equipmentTags.length;

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <Factory className="w-5 h-5 text-rose-500" />
        장비 태그 인식
        <InfoTooltip
          content="P&ID 도면에서 산업별 장비 태그를 OCR과 패턴 매칭으로 자동 인식합니다."
          position="right"
        />
        {totalCount > 0 && (
          <span className="ml-auto text-sm font-normal text-gray-500">
            {verifiedCount}/{totalCount} 검증됨
          </span>
        )}
      </h2>

      {/* 프로파일 선택 */}
      <div className="mb-4">
        <button
          onClick={() => setIsProfileOpen(!isProfileOpen)}
          className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-rose-500" />
            <span className="text-sm font-medium">
              {selectedProfile?.name || '프로파일 선택'}
            </span>
          </div>
          {isProfileOpen ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {isProfileOpen && (
          <div className="mt-2 border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            {availableProfiles.map((profile) => (
              <button
                key={profile.id}
                onClick={() => {
                  onSelectProfile(profile.id);
                  setIsProfileOpen(false);
                }}
                className={`w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  selectedProfile?.id === profile.id
                    ? 'bg-rose-50 dark:bg-rose-900/20'
                    : ''
                }`}
              >
                <div className="text-sm font-medium">{profile.name}</div>
                <div className="text-xs text-gray-500">{profile.description}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 검색 */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="태그 검색 (예: ECU, FMU-001)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-rose-500 focus:border-rose-500 dark:bg-gray-700"
        />
      </div>

      {/* 장비 목록 */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">
          <div className="animate-spin w-8 h-8 border-2 border-rose-500 border-t-transparent rounded-full mx-auto mb-2" />
          장비 태그 분석 중...
        </div>
      ) : totalCount === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <Factory className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p className="text-sm">검출된 장비 태그가 없습니다.</p>
          <p className="text-xs mt-1">프로파일을 선택하고 분석을 실행하세요.</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {Object.entries(groupedByType).map(([type, tags]) => (
            <div
              key={type}
              className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden"
            >
              <button
                onClick={() => toggleType(type)}
                className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-rose-600 dark:text-rose-400">
                    {type}
                  </span>
                  <span className="text-xs text-gray-500">({tags.length}개)</span>
                </div>
                {expandedTypes.has(type) ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {expandedTypes.has(type) && (
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {tags.map((tag) => (
                    <div
                      key={tag.id}
                      className="flex items-center justify-between px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm">{tag.tag}</span>
                        {tag.fullName && (
                          <span className="text-xs text-gray-500">
                            ({tag.fullName})
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs px-2 py-0.5 rounded ${
                            tag.confidence >= 0.9
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : tag.confidence >= 0.7
                              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}
                        >
                          {(tag.confidence * 100).toFixed(0)}%
                        </span>
                        <button
                          onClick={() => onVerifyTag(tag.id, !tag.verified)}
                          className={`px-2 py-0.5 text-xs rounded transition-colors ${
                            tag.verified
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-200 text-gray-600 hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-300'
                          }`}
                        >
                          {tag.verified ? '검증됨' : '검증'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 내보내기 버튼 */}
      {totalCount > 0 && (
        <div className="mt-4 flex gap-2">
          <button
            onClick={() => onExport('excel')}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-rose-500 text-white rounded-lg hover:bg-rose-600 transition-colors text-sm"
          >
            <Download className="w-4 h-4" />
            Excel
          </button>
          <button
            onClick={() => onExport('csv')}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={() => onExport('json')}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
          >
            <Download className="w-4 h-4" />
            JSON
          </button>
        </div>
      )}
    </section>
  );
}
