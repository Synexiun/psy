import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { MainTabLayout } from '@components/MainTabLayout';
import { CrisisScreen } from '@features/intervention/screens/CrisisScreen';
import { ToolDetailScreen } from '@features/intervention/screens/ToolDetailScreen';
import { JournalEntryScreen } from '@features/memory/screens/JournalEntryScreen';
import { AssessmentListScreen } from '@features/assessment/screens/AssessmentListScreen';
import { AssessmentSessionScreen } from '@features/assessment/screens/AssessmentSessionScreen';

/**
 * Root navigation stack.
 *
 * Structure:
 *   MainTabs          ← custom tab shell (Home / CheckIn / Tools / Journal)
 *   Crisis            ← full-screen; no animation, no back gesture (T3 rule)
 *   ToolDetail        ← full-screen tool runner; pushed from ToolsScreen
 *   JournalEntry      ← full-screen text editor; pushed from JournalScreen
 *
 * Why not @react-navigation/bottom-tabs?
 *   The package is not in package.json. We implement tab switching via
 *   MainTabLayout + BottomTabBar (pure View + useState) which is sufficient
 *   for this phase and avoids introducing an unvetted dependency.
 *
 * Crisis screen rules (CLAUDE.md §1 — T3/T4 crisis flows):
 *   - animation: 'none' — no delay, no distraction.
 *   - gestureEnabled: false — cannot be accidentally swiped away.
 *   - headerShown: false — no back button that could cause confusion.
 *   - These props must never be changed without clinical QA sign-off.
 */
export type RootStackParamList = {
  MainTabs: undefined;
  Crisis: undefined;
  ToolDetail: { toolId: string };
  JournalEntry: undefined;
  AssessmentList: undefined;
  AssessmentSession: { instrumentId: import('@features/assessment/store').InstrumentId };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 2 },
  },
});

// React Navigation 7 types are built against React 19; RN 0.76 uses React 18.
const SafeNavigationContainer = NavigationContainer as unknown as React.FC<any>;
const SafeStackNavigator = Stack.Navigator as unknown as React.FC<any>;

export function App() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <SafeNavigationContainer>
          <SafeStackNavigator initialRouteName="MainTabs" screenOptions={{ headerShown: false }}>
            <Stack.Screen name="MainTabs" component={MainTabLayout} />
            <Stack.Screen
              name="Crisis"
              component={CrisisScreen}
              options={{
                animation: 'none',
                gestureEnabled: false,
                headerShown: false,
              }}
            />
            <Stack.Screen
              name="ToolDetail"
              component={ToolDetailScreen}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="JournalEntry"
              component={JournalEntryScreen}
              options={{
                headerShown: false,
                animation: 'slide_from_bottom',
              }}
            />
            <Stack.Screen
              name="AssessmentList"
              component={AssessmentListScreen}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="AssessmentSession"
              component={AssessmentSessionScreen}
              options={{ headerShown: false }}
            />
          </SafeStackNavigator>
        </SafeNavigationContainer>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
