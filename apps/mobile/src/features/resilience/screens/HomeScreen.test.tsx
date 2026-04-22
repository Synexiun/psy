import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { HomeScreen } from './HomeScreen';
import { CrisisScreen } from '@features/intervention/screens/CrisisScreen';
import { UrgeLogScreen } from '@features/intervention/screens/UrgeLogScreen';

const Stack = createNativeStackNavigator();

// React Navigation 7 types are built against React 19; RN 0.76 uses React 18.
const SafeNavigationContainer = NavigationContainer as unknown as React.FC<any>;
const SafeStackNavigator = Stack.Navigator as unknown as React.FC<any>;

function TestRoot() {
  return (
    <SafeNavigationContainer>
      <SafeStackNavigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="UrgeLog" component={UrgeLogScreen} />
        <Stack.Screen name="Crisis" component={CrisisScreen} />
      </SafeStackNavigator>
    </SafeNavigationContainer>
  );
}

describe('HomeScreen', () => {
  it('renders resilience and continuous streaks', () => {
    render(<TestRoot />);
    expect(screen.getByText('Resilience')).toBeTruthy();
    expect(screen.getByText('Continuous')).toBeTruthy();
  });

  it('navigates to UrgeLog on primary action', async () => {
    render(<TestRoot />);
    const button = screen.getByText('Log an urge');
    fireEvent.press(button);
    await waitFor(() => {
      expect(screen.getByText('Log an urge')).toBeTruthy();
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
});
