import { render, screen } from '@testing-library/react-native';
import { CrisisScreen } from './CrisisScreen';

describe('CrisisScreen', () => {
  it('renders headline', () => {
    render(<CrisisScreen />);
    expect(screen.getByText("You're here. That matters.")).toBeTruthy();
  });

  it('renders deterministic tools without network dependency', () => {
    render(<CrisisScreen />);
    expect(screen.getByLabelText('Start urge surf')).toBeTruthy();
    expect(screen.getByLabelText('Start TIPP')).toBeTruthy();
    expect(screen.getByLabelText('Call support contact')).toBeTruthy();
  });

  it('renders hotline information', () => {
    render(<CrisisScreen />);
    expect(screen.getByLabelText('Crisis hotline 988')).toBeTruthy();
  });
});
