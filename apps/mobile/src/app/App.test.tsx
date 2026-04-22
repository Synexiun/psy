import { render, screen } from '@testing-library/react-native';
import { App } from './App';

describe('App', () => {
  it('renders the home screen by default', () => {
    render(<App />);
    expect(screen.getByText('Resilience')).toBeTruthy();
    expect(screen.getByText('Continuous')).toBeTruthy();
  });
});
