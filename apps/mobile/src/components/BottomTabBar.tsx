/**
 * BottomTabBar — persistent tab bar rendered below the active screen.
 *
 * Built without @react-navigation/bottom-tabs (not in package.json).
 * Implemented as a pure View component; the active tab is tracked in
 * MainTabLayout which controls which screen is rendered.
 *
 * Design constraints:
 *  - Min touch target: 44×44 pt (CLAUDE.md accessibility).
 *  - Crisis tab is always visible and uses a distinct appearance to signal
 *    its priority — but NOT red/alarm color. CrisisScreen itself follows the
 *    "never alarm color" rule; the tab icon uses the standard graphite/slate
 *    palette so as not to cause anxiety on every app open.
 *  - No external icon library; unicode characters used for icons.
 */

import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { color, size, space } from '@theme/tokens';

export type TabId = 'Home' | 'CheckIn' | 'Tools' | 'Journal' | 'Crisis';

interface TabConfig {
  id: TabId;
  label: string;
  icon: string;
  accessibilityLabel: string;
}

export const TAB_CONFIG: TabConfig[] = [
  {
    id: 'Home',
    label: 'Home',
    icon: '⌂',
    accessibilityLabel: 'Home tab',
  },
  {
    id: 'CheckIn',
    label: 'Check-in',
    icon: '+',
    accessibilityLabel: 'Check-in tab — log an urge',
  },
  {
    id: 'Tools',
    label: 'Tools',
    icon: '⊞',
    accessibilityLabel: 'Coping tools tab',
  },
  {
    id: 'Journal',
    label: 'Journal',
    icon: '≡',
    accessibilityLabel: 'Journal tab',
  },
  {
    id: 'Crisis',
    label: 'Support',
    icon: '●',
    accessibilityLabel: 'Get support now — opens crisis tools',
  },
];

interface BottomTabBarProps {
  activeTab: TabId;
  onTabPress: (tabId: TabId) => void;
}

export function BottomTabBar({ activeTab, onTabPress }: BottomTabBarProps) {
  return (
    <View style={styles.container}>
      {TAB_CONFIG.map((tab) => {
        const isActive = tab.id === activeTab;
        const isCrisis = tab.id === 'Crisis';

        return (
          <TouchableOpacity
            key={tab.id}
            style={styles.tab}
            onPress={() => onTabPress(tab.id)}
            activeOpacity={0.7}
            accessibilityRole="tab"
            accessibilityLabel={tab.accessibilityLabel}
            accessibilityState={{ selected: isActive }}
          >
            <Text
              style={[
                styles.icon,
                isActive && styles.iconActive,
                isCrisis && styles.iconCrisis,
                isCrisis && isActive && styles.iconCrisisActive,
              ]}
              aria-hidden
            >
              {tab.icon}
            </Text>
            <Text
              style={[
                styles.label,
                isActive && styles.labelActive,
                isCrisis && styles.labelCrisis,
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: color.offWhite,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: color.mist,
    // Safe-area bottom padding is handled by the parent (SafeAreaView).
    paddingBottom: space.xs,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
    paddingVertical: space.xs,
    gap: 2,
  },
  icon: {
    fontSize: 20,
    color: color.slate,
    lineHeight: 24,
  },
  iconActive: {
    color: color.signalBlue,
  },
  iconCrisis: {
    color: color.slate,
  },
  iconCrisisActive: {
    color: color.graphite,
  },
  label: {
    fontSize: size.caption,
    color: color.slate,
  },
  labelActive: {
    color: color.signalBlue,
  },
  labelCrisis: {
    // Intentionally same as inactive — crisis tab should not feel alarming on every view.
    color: color.slate,
  },
});
