/**
 * MainTabLayout — renders the active tab screen + persistent bottom tab bar.
 *
 * Architecture note: @react-navigation/bottom-tabs is not in package.json.
 * This component is the tab shell; it is rendered as the "MainTabs" screen
 * inside the root NativeStackNavigator. Modal-style screens (Crisis,
 * ToolDetail, JournalEntry) are pushed onto the root stack above this shell,
 * so they get a full-screen native presentation.
 *
 * Tab switching is O(1) and works entirely offline — no navigation event is
 * fired, just a React setState. This is important because:
 *   - The CrisisScreen is accessible from HomeScreen via root stack (preserves
 *     the gesture-disabled, animation-none presentation required by T3 rules).
 *   - The Crisis tab in the bottom bar navigates to the root stack Crisis
 *     screen (same rules apply).
 */

import React, { useCallback, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { BottomTabBar } from '@components/BottomTabBar';
import { TabSwitchProvider } from '@components/TabSwitchContext';
import type { TabId } from '@components/BottomTabBar';

import { HomeScreen } from '@features/resilience/screens/HomeScreen';
import { UrgeLogScreen } from '@features/intervention/screens/UrgeLogScreen';
import { ToolsScreen } from '@features/intervention/screens/ToolsScreen';
import { JournalScreen } from '@features/memory/screens/JournalScreen';

import type { RootStackParamList } from '@app/App';

const INITIAL_TAB: TabId = 'Home';

export function MainTabLayout() {
  const [activeTab, setActiveTab] = useState<TabId>(INITIAL_TAB);
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const insets = useSafeAreaInsets();

  const handleTabPress = useCallback(
    (tabId: TabId) => {
      if (tabId === 'Crisis') {
        // Crisis always pushes onto the root stack — deterministic, gesture-disabled,
        // no animation (T3 crisis flow rules: CLAUDE.md §1).
        navigation.navigate('Crisis');
        return;
      }
      setActiveTab(tabId);
    },
    [navigation],
  );

  // tabSwitchValue is stable until handleTabPress changes (navigation ref is stable).
  const tabSwitchValue = useMemo(
    () => ({ switchTab: handleTabPress }),
    [handleTabPress],
  );

  return (
    <TabSwitchProvider value={tabSwitchValue}>
      <View style={[styles.root, { paddingBottom: insets.bottom }]}>
        {/* Active screen — only the current tab is mounted */}
        <View style={styles.screenContainer}>
          {activeTab === 'Home' && <HomeScreen />}
          {activeTab === 'CheckIn' && <UrgeLogScreen />}
          {activeTab === 'Tools' && <ToolsScreen />}
          {activeTab === 'Journal' && <JournalScreen />}
        </View>

        {/* Persistent bottom tab bar */}
        <BottomTabBar activeTab={activeTab} onTabPress={handleTabPress} />
      </View>
    </TabSwitchProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  screenContainer: {
    flex: 1,
  },
});
