import 'react-native-gesture-handler/jestSetup';

jest.mock('react-native-mmkv', () => ({
  MMKV: class MockMMKV {
    constructor() {}
    getString() { return undefined; }
    set() {}
    delete() {}
  },
}));

jest.mock('expo', () => ({
  registerRootComponent: jest.fn(),
}));

jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  const SafeAreaInsetsContext = React.createContext({ top: 0, bottom: 0, left: 0, right: 0 });
  const SafeAreaFrameContext = React.createContext({ x: 0, y: 0, width: 320, height: 640 });
  return {
    SafeAreaProvider: ({ children, initialMetrics }) => {
      const insets = initialMetrics?.insets ?? { top: 0, bottom: 0, left: 0, right: 0 };
      const frame = initialMetrics?.frame ?? { x: 0, y: 0, width: 320, height: 640 };
      return React.createElement(
        SafeAreaFrameContext.Provider,
        { value: frame },
        React.createElement(
          SafeAreaInsetsContext.Provider,
          { value: insets },
          children,
        ),
      );
    },
    SafeAreaView: ({ children }) => children,
    useSafeAreaInsets: () => React.useContext(SafeAreaInsetsContext),
    useSafeAreaFrame: () => React.useContext(SafeAreaFrameContext),
    SafeAreaInsetsContext,
    SafeAreaFrameContext,
  };
});

jest.useFakeTimers();
