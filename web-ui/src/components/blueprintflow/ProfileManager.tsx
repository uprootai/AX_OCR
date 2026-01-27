/**
 * ProfileManager Component
 * 프로파일 선택 및 관리 (추가/수정/삭제)
 */

import { useState, useMemo } from 'react';
import { Zap, Plus, Pencil, Trash2, Save, X, HelpCircle, ChevronDown, ChevronUp, Copy } from 'lucide-react';
import { useProfileStore, type UserProfile, type ProfileParams } from '../../store/profileStore';
import type { NodeDefinition, NodeParameter } from '../../config/nodes/types';

interface ProfileManagerProps {
  nodeType: string;
  definition: NodeDefinition;
  currentParams: Record<string, unknown>;
  selectedProfile: string | undefined;
  onProfileSelect: (profileName: string, params: ProfileParams) => void;
  onParamsChange: (params: Record<string, unknown>) => void;
}

interface ProfileFormData {
  name: string;
  label: string;
  description: string;
}

export function ProfileManager({
  nodeType,
  definition,
  currentParams,
  selectedProfile,
  onProfileSelect,
}: ProfileManagerProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editingProfile, setEditingProfile] = useState<string | null>(null);
  const [formData, setFormData] = useState<ProfileFormData>({
    name: '',
    label: '',
    description: '',
  });
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const { userProfiles, addProfile, updateProfile, deleteProfile } = useProfileStore();

  // 빌트인 프로파일 + 사용자 프로파일 병합
  const allProfiles = useMemo(() => {
    const builtIn = (definition.profiles?.available || []).map((p) => ({
      ...p,
      isBuiltIn: true,
      createdAt: '',
      updatedAt: '',
    }));
    const user = userProfiles[nodeType] || [];
    return [...builtIn, ...user];
  }, [definition.profiles, userProfiles, nodeType]);

  // 현재 선택된 프로파일 정보 (선택 안됐으면 기본값 사용)
  const effectiveSelectedProfile = selectedProfile || definition.profiles?.default;
  const currentProfile = useMemo(() => {
    return allProfiles.find((p) => p.name === effectiveSelectedProfile);
  }, [allProfiles, effectiveSelectedProfile]);

  // 프로파일 선택 핸들러
  const handleProfileSelect = (profileName: string) => {
    const profile = allProfiles.find((p) => p.name === profileName);
    if (profile) {
      onProfileSelect(profileName, profile.params);
    }
  };

  // 새 프로파일 추가 시작
  const handleStartAdd = () => {
    const timestamp = Date.now().toString(36);
    setFormData({
      name: `custom_${timestamp}`,
      label: '새 프리셋',
      description: '현재 파라미터 설정',
    });
    setEditingProfile(null);
    setIsEditing(true);
  };

  // 프로파일 수정 시작
  const handleStartEdit = (profile: UserProfile) => {
    if (profile.isBuiltIn) return; // 빌트인은 수정 불가
    setFormData({
      name: profile.name,
      label: profile.label,
      description: profile.description,
    });
    setEditingProfile(profile.name);
    setIsEditing(true);
  };

  // 빌트인 프로파일 복제
  const handleDuplicate = (profile: { name: string; label: string; description: string; params: ProfileParams }) => {
    const timestamp = Date.now().toString(36);
    setFormData({
      name: `${profile.name}_copy_${timestamp}`,
      label: `${profile.label} (복사본)`,
      description: profile.description,
    });
    // 복제 시 해당 프로파일의 params를 currentParams로 적용
    onProfileSelect(profile.name, profile.params);
    setEditingProfile(null);
    setIsEditing(true);
  };

  // 프로파일 저장
  const handleSave = () => {
    if (!formData.label.trim()) return;

    // 현재 파라미터에서 프로파일에 저장할 값 추출
    const paramsToSave: ProfileParams = {};
    definition.parameters.forEach((param: NodeParameter) => {
      if (currentParams[param.name] !== undefined) {
        paramsToSave[param.name] = currentParams[param.name] as string | number | boolean;
      } else if (param.default !== undefined) {
        paramsToSave[param.name] = param.default as string | number | boolean;
      }
    });

    if (editingProfile) {
      // 수정
      updateProfile(nodeType, editingProfile, {
        label: formData.label,
        description: formData.description,
        params: paramsToSave,
      });
    } else {
      // 추가
      addProfile(nodeType, {
        name: formData.name,
        label: formData.label,
        description: formData.description,
        params: paramsToSave,
      });
    }

    setIsEditing(false);
    setEditingProfile(null);

    // 새로 추가한 프로파일 선택
    if (!editingProfile) {
      onProfileSelect(formData.name, paramsToSave);
    }
  };

  // 프로파일 삭제
  const handleDelete = (profileName: string) => {
    deleteProfile(nodeType, profileName);
    setShowDeleteConfirm(null);

    // 삭제된 프로파일이 선택되어 있었으면 기본 프로파일로 변경
    if (effectiveSelectedProfile === profileName && definition.profiles?.default) {
      const defaultProfile = allProfiles.find((p) => p.name === definition.profiles?.default);
      if (defaultProfile) {
        onProfileSelect(defaultProfile.name, defaultProfile.params);
      }
    }
  };

  // 취소
  const handleCancel = () => {
    setIsEditing(false);
    setEditingProfile(null);
  };

  if (!definition.profiles || allProfiles.length === 0) {
    return null;
  }

  return (
    <div className="p-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-lg border border-purple-200 dark:border-purple-700">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-purple-500" />
          <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">
            프로파일 (기본값 프리셋)
          </span>
          <span className="text-xs text-purple-500 dark:text-purple-400">
            ({allProfiles.length}개)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-purple-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-purple-500" />
        )}
      </div>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {/* 편집 모드 */}
          {isEditing ? (
            <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-purple-300 dark:border-purple-600 space-y-3">
              <div className="text-xs font-semibold text-purple-700 dark:text-purple-300">
                {editingProfile ? '프로파일 수정' : '새 프로파일 저장'}
              </div>

              <div className="space-y-2">
                <div>
                  <label className="text-xs text-gray-600 dark:text-gray-400">이름</label>
                  <input
                    type="text"
                    value={formData.label}
                    onChange={(e) => setFormData({ ...formData, label: e.target.value })}
                    placeholder="프리셋 이름"
                    className="w-full mt-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-600 dark:text-gray-400">설명</label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="프리셋 설명"
                    className="w-full mt-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className="p-2 bg-purple-50 dark:bg-purple-900/30 rounded text-xs text-purple-700 dark:text-purple-300">
                <strong>저장될 파라미터:</strong>
                <div className="mt-1 font-mono text-[10px] max-h-20 overflow-y-auto">
                  {definition.parameters.slice(0, 5).map((param: NodeParameter) => (
                    <div key={param.name}>
                      {param.name}: {String(currentParams[param.name] ?? param.default)}
                    </div>
                  ))}
                  {definition.parameters.length > 5 && (
                    <div className="text-purple-500">... +{definition.parameters.length - 5}개 더</div>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={!formData.label.trim()}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-3 h-3" />
                  저장
                </button>
                <button
                  onClick={handleCancel}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-500"
                >
                  <X className="w-3 h-3" />
                  취소
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* 프로파일 선택 + 관리 버튼 */}
              <div className="space-y-2">
                <select
                  value={effectiveSelectedProfile}
                  onChange={(e) => handleProfileSelect(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-700 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <optgroup label="기본 제공">
                    {allProfiles
                      .filter((p) => p.isBuiltIn)
                      .map((profile) => (
                        <option key={profile.name} value={profile.name}>
                          {profile.label}
                        </option>
                      ))}
                  </optgroup>
                  {allProfiles.some((p) => !p.isBuiltIn) && (
                    <optgroup label="사용자 정의">
                      {allProfiles
                        .filter((p) => !p.isBuiltIn)
                        .map((profile) => (
                          <option key={profile.name} value={profile.name}>
                            {profile.label}
                          </option>
                        ))}
                    </optgroup>
                  )}
                </select>

                {/* 관리 버튼 - 항상 표시 */}
                <div className="flex gap-1">
                  <button
                    onClick={handleStartAdd}
                    className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/40 hover:bg-purple-200 dark:hover:bg-purple-800/50 rounded transition-colors"
                    title="현재 설정을 새 프리셋으로 저장"
                  >
                    <Plus className="w-3 h-3" />
                    추가
                  </button>
                  {currentProfile && (
                    <>
                      {currentProfile.isBuiltIn ? (
                        // 빌트인 프로파일: 복제만 가능
                        <button
                          onClick={() => handleDuplicate(currentProfile)}
                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/40 hover:bg-blue-200 dark:hover:bg-blue-800/50 rounded transition-colors"
                          title="이 프로파일을 복제하여 수정"
                        >
                          <Copy className="w-3 h-3" />
                          복제
                        </button>
                      ) : (
                        // 사용자 정의 프로파일: 수정/삭제 가능
                        <>
                          <button
                            onClick={() => handleStartEdit(currentProfile as UserProfile)}
                            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/40 hover:bg-green-200 dark:hover:bg-green-800/50 rounded transition-colors"
                          >
                            <Pencil className="w-3 h-3" />
                            수정
                          </button>
                          {showDeleteConfirm === currentProfile.name ? (
                            <div className="flex-1 flex gap-1">
                              <button
                                onClick={() => handleDelete(currentProfile.name)}
                                className="flex-1 px-2 py-1.5 text-xs font-medium bg-red-500 text-white rounded hover:bg-red-600"
                              >
                                확인
                              </button>
                              <button
                                onClick={() => setShowDeleteConfirm(null)}
                                className="flex-1 px-2 py-1.5 text-xs font-medium bg-gray-300 dark:bg-gray-600 rounded hover:bg-gray-400"
                              >
                                취소
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setShowDeleteConfirm(currentProfile.name)}
                              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-800/50 rounded transition-colors"
                            >
                              <Trash2 className="w-3 h-3" />
                              삭제
                            </button>
                          )}
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* 선택된 프로파일 정보 */}
              {currentProfile && (
                <div className="space-y-2">
                  <div className="flex items-start gap-2 text-xs text-purple-600 dark:text-purple-400">
                    <HelpCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <span>{currentProfile.description}</span>
                      {currentProfile.isBuiltIn && (
                        <span className="ml-2 px-1.5 py-0.5 text-[10px] bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                          기본 제공
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 프로파일 값 미리보기 */}
                  <div className="p-2 bg-white dark:bg-gray-800 rounded border border-purple-200 dark:border-purple-700">
                    <div className="text-[10px] font-semibold text-purple-600 dark:text-purple-400 mb-1">
                      적용된 값:
                    </div>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px] font-mono">
                      {Object.entries(currentProfile.params).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">{key}:</span>
                          <span className="text-purple-700 dark:text-purple-300 font-semibold">
                            {String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* 안내 메시지 */}
              <div className="text-[10px] text-purple-500 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/30 p-2 rounded">
                프로파일 선택 시 아래 파라미터가 자동 변경됩니다. 개별 파라미터를 수정하면 프로파일 값을 덮어씁니다.
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
