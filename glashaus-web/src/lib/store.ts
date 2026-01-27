import { create } from 'zustand';

interface GlashausState {
  activeCaseId: number | null;
  setActiveCase: (id: number) => void;
  reset: () => void;
}

export const useStore = create<GlashausState>((set) => ({
  activeCaseId: null,
  setActiveCase: (id) => set({ activeCaseId: id }),
  reset: () => set({ activeCaseId: null }),
}));
