/**
 * TabSwitchContext — allows nested screens (e.g. HomeScreen) to switch the
 * active bottom tab without coupling to the tab layout implementation.
 *
 * Usage:
 *   const { switchTab } = useTabSwitch();
 *   switchTab('CheckIn');
 */

import React, { createContext, useContext } from 'react';
import type { TabId } from '@components/BottomTabBar';

interface TabSwitchContextValue {
  switchTab: (tabId: TabId) => void;
}

const TabSwitchContext = createContext<TabSwitchContextValue>({
  switchTab: () => undefined,
});

export const TabSwitchProvider = TabSwitchContext.Provider;

export function useTabSwitch(): TabSwitchContextValue {
  return useContext(TabSwitchContext);
}
