import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { JobFilters } from '../types/job';

type AppState = {
  onboardingDone: boolean;
  preferredCategories: string[];
  savedJobIds: number[];
  filters: JobFilters;
  setOnboardingDone: (done: boolean) => void;
  setPreferredCategories: (cats: string[]) => void;
  toggleSaved: (jobId: number) => void;
  setFilters: (filters: JobFilters) => void;
  clearFilters: () => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      onboardingDone: false,
      preferredCategories: [],
      savedJobIds: [],
      filters: {},
      setOnboardingDone: (done) => set({ onboardingDone: done }),
      setPreferredCategories: (cats) => set({ preferredCategories: cats }),
      toggleSaved: (jobId) => {
        const current = get().savedJobIds;
        set({
          savedJobIds: current.includes(jobId)
            ? current.filter((id) => id !== jobId)
            : [...current, jobId],
        });
      },
      setFilters: (filters) => set({ filters }),
      clearFilters: () => set({ filters: {} }),
    }),
    {
      name: 'haunsla-store',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        onboardingDone: state.onboardingDone,
        preferredCategories: state.preferredCategories,
        savedJobIds: state.savedJobIds,
      }),
    },
  ),
);
