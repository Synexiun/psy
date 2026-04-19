import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { CrisisScreen } from '@features/intervention/screens/CrisisScreen';
import { HomeScreen } from '@features/resilience/screens/HomeScreen';
import { UrgeLogScreen } from '@features/intervention/screens/UrgeLogScreen';

export type RootStackParamList = {
  Home: undefined;
  UrgeLog: undefined;
  Crisis: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 2 },
  },
});

export function App() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <NavigationContainer>
          <Stack.Navigator initialRouteName="Home">
            <Stack.Screen name="Home" component={HomeScreen} />
            <Stack.Screen name="UrgeLog" component={UrgeLogScreen} />
            <Stack.Screen
              name="Crisis"
              component={CrisisScreen}
              options={{ animation: 'none', gestureEnabled: false }}
            />
          </Stack.Navigator>
        </NavigationContainer>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
