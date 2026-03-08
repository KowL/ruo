import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SidebarState {
    isVisible: boolean;
    toggleSidebar: () => void;
    setVisible: (visible: boolean) => void;
}

export const useSidebarStore = create<SidebarState>()(
    persist(
        (set) => ({
            isVisible: true,
            toggleSidebar: () => set((state) => ({ isVisible: !state.isVisible })),
            setVisible: (visible) => set({ isVisible: visible }),
        }),
        {
            name: 'sidebar-storage',
        }
    )
);
