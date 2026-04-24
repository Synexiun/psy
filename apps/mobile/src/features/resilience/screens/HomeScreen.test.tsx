import React, { useState } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { HomeScreen } from './HomeScreen';
import { CrisisScreen } from '@features/intervention/screens/CrisisScreen';
import { TabSwitchProvider } from '@components/TabSwitchContext';
import type { TabId } from '@components/BottomTabBar';

const Stack = createNativeStackNavigator();

// React Navigation 7 types are built against React 19; RN 0.76 uses React 18.
const SafeNavigationContainer = NavigationContainer as unknown as React.FC<any>;
const SafeStackNavigator = Stack.Navigator as unknown as React.FC<any>;

/**
 * Minimal test harness that wraps HomeScreen with the tab switch context and a
 * root stack that includes CrisisScreen so navigation tests can verify the
 * resulting screen.
 */
function TestRoot({ onSwitchTab }: { onSwitchTab?: (tabId: TabId) => void }) {
  const [switchedTab, setSwitchedTab] = useState<TabId | null>(null);

  const switchTab = (tabId: TabId) => {
    setSwitchedTab(tabId);
    onSwitchTab?.(tabId);
  };

  return (
    <TabSwitchProvider value={{ switchTab }}>
      <SafeNavigationContainer>
        <SafeStackNavigator initialRouteName="Home">
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="Crisis" component={CrisisScreen} />
        </SafeStackNavigator>
      </SafeNavigationContainer>
    </TabSwitchProvider>
  );
}

describe('HomeScreen', () => {
  it('renders resilience and continuous streaks', () => {
    render(<TestRoot />);
    expect(screen.getByText('Resilience')).toBeTruthy();
    expect(screen.getByText('Continuous')).toBeTruthy();
  });

  it('renders recent patterns section', () => {
    render(<TestRoot />);
    expect(screen.getByText('Recent patterns')).toBeTruthy();
  });

  it('calls switchTab with CheckIn when Check in button is pressed', async () => {
    const onSwitchTab = jest.fn();
    render(<TestRoot onSwitchTab={onSwitchTab} />);
    const button = screen.getByText('Check in');
    fireEvent.press(button);
    await waitFor(() => {
      expect(onSwitchTab).toHaveBeenCalledWith('CheckIn');
    });
  });

  it('navigates to Crisis on SOS action', async () => {
    render(<TestRoot />);
    const button = screen.getByText('Need help now');
    fireEvent.press(button);
    await waitFor(() => {
      expect(screen.getByText("You're here. That matters.")).toBeTruthy();
    });
  });

  it('crisis button has accessibility label', () => {
    render(<TestRoot />);
    expect(
      screen.getByLabelText('Need help now — open crisis support tools'),
    ).toBeTruthy();
  });
});
