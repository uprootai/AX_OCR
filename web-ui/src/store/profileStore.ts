/**
 * Profile Store
 * 사용자 정의 프로파일 관리 (localStorage 영속화)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ProfileParams {
  [key: string]: string | number | boolean;
}

export interface UserProfile {
  name: string;
  label: string;
  description: string;
  params: ProfileParams;
  isBuiltIn: boolean;
  createdAt: string;
  updatedAt: string;
}

interface ProfileStore {
  // 노드 타입별 사용자 정의 프로파일
  userProfiles: Record<string, UserProfile[]>;

  // Actions
  addProfile: (nodeType: string, profile: Omit<UserProfile, 'isBuiltIn' | 'createdAt' | 'updatedAt'>) => void;
  updateProfile: (nodeType: string, profileName: string, updates: Partial<Omit<UserProfile, 'name' | 'isBuiltIn'>>) => void;
  deleteProfile: (nodeType: string, profileName: string) => void;
  getProfiles: (nodeType: string) => UserProfile[];
  hasProfile: (nodeType: string, profileName: string) => boolean;
}

export const useProfileStore = create<ProfileStore>()(
  persist(
    (set, get) => ({
      userProfiles: {},

      addProfile: (nodeType, profile) => {
        const now = new Date().toISOString();
        const newProfile: UserProfile = {
          ...profile,
          isBuiltIn: false,
          createdAt: now,
          updatedAt: now,
        };

        set((state) => ({
          userProfiles: {
            ...state.userProfiles,
            [nodeType]: [...(state.userProfiles[nodeType] || []), newProfile],
          },
        }));
      },

      updateProfile: (nodeType, profileName, updates) => {
        set((state) => ({
          userProfiles: {
            ...state.userProfiles,
            [nodeType]: (state.userProfiles[nodeType] || []).map((p) =>
              p.name === profileName
                ? { ...p, ...updates, updatedAt: new Date().toISOString() }
                : p
            ),
          },
        }));
      },

      deleteProfile: (nodeType, profileName) => {
        set((state) => ({
          userProfiles: {
            ...state.userProfiles,
            [nodeType]: (state.userProfiles[nodeType] || []).filter(
              (p) => p.name !== profileName
            ),
          },
        }));
      },

      getProfiles: (nodeType) => {
        return get().userProfiles[nodeType] || [];
      },

      hasProfile: (nodeType, profileName) => {
        return (get().userProfiles[nodeType] || []).some((p) => p.name === profileName);
      },
    }),
    {
      name: 'blueprintflow-profiles',
    }
  )
);
