/**
 * AssessmentSessionScreen — unit tests.
 *
 * Covers:
 * - Renders first question text for PHQ-9
 * - Renders preamble on first question
 * - "Next" button is disabled when no response selected
 * - Selecting a response enables "Next"
 * - Progress label renders current / total
 * - PHQ-9 item 9: safety message shown when value > 0
 * - "Get support now" button on safety card navigates to Crisis
 * - "Submit" label appears on last question
 *
 * Navigation is provided via a real NavigationContainer + test stack so that
 * useNavigation and useRoute hooks work without extra mocking.
 */

import React from 'react';
import {
  render,
  screen,
  fireEvent,
  waitFor,
} from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { AssessmentSessionScreen } from './AssessmentSessionScreen';
import { CrisisScreen } from '@features/intervention/screens/CrisisScreen';
import { useAssessment } from '@features/assessment/store';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const Stack = createNativeStackNavigator();

// React Navigation 7 types are built against React 19; RN 0.76 uses React 18.
const SafeNavigationContainer = NavigationContainer as unknown as React.FC<any>;
const SafeStackNavigator = Stack.Navigator as unknown as React.FC<any>;

type TestRootProps = {
  instrumentId?: 'phq9' | 'gad7' | 'who5';
};

/**
 * Wraps AssessmentSessionScreen in a minimal stack so that
 * useNavigation/useRoute work correctly.
 */
function TestRoot({ instrumentId = 'phq9' }: TestRootProps) {
  function AssessmentWrapper() {
    return <AssessmentSessionScreen />;
  }

  return (
    <SafeNavigationContainer>
      <SafeStackNavigator
        initialRouteName="AssessmentSession"
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen
          name="AssessmentSession"
          component={AssessmentWrapper}
          initialParams={{ instrumentId }}
        />
        <Stack.Screen name="Crisis" component={CrisisScreen} />
      </SafeStackNavigator>
    </SafeNavigationContainer>
  );
}

/** Reset the assessment store before each test. */
function resetStore() {
  useAssessment.setState({
    currentInstrumentId: null,
    responses: {},
    lastScores: {},
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AssessmentSessionScreen', () => {
  beforeEach(resetStore);

  // 1. Renders first question text for PHQ-9
  it('renders the first PHQ-9 item text', () => {
    render(<TestRoot instrumentId="phq9" />);
    expect(
      screen.getByText('Little interest or pleasure in doing things'),
    ).toBeTruthy();
  });

  // 2. Renders preamble on first question (PHQ-9)
  it('shows the 2-week preamble on the first PHQ-9 question', () => {
    render(<TestRoot instrumentId="phq9" />);
    expect(
      screen.getByText(
        'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
      ),
    ).toBeTruthy();
  });

  // 3. Progress label
  it('shows progress label "1 / 9" for PHQ-9 first question', () => {
    render(<TestRoot instrumentId="phq9" />);
    expect(screen.getByText('1 / 9')).toBeTruthy();
  });

  // 4. "Next" is disabled when no response selected
  it('"Next" button is disabled before any response is selected', () => {
    render(<TestRoot instrumentId="phq9" />);
    const nextBtn = screen.getByLabelText('Next question');
    expect(nextBtn.props.accessibilityState?.disabled).toBe(true);
  });

  // 5. Selecting a response enables "Next"
  it('selecting a response option enables "Next"', async () => {
    render(<TestRoot instrumentId="phq9" />);
    const option = screen.getByLabelText('Not at all');
    fireEvent.press(option);
    await waitFor(() => {
      const nextBtn = screen.getByLabelText('Next question');
      expect(nextBtn.props.accessibilityState?.disabled).toBe(false);
    });
  });

  // 6. Pressing "Next" advances to question 2
  it('pressing "Next" advances to the second question', async () => {
    render(<TestRoot instrumentId="phq9" />);
    fireEvent.press(screen.getByLabelText('Not at all'));
    await waitFor(() => {
      expect(screen.getByLabelText('Next question').props.accessibilityState?.disabled).toBe(false);
    });
    fireEvent.press(screen.getByLabelText('Next question'));
    await waitFor(() => {
      expect(screen.getByText('2 / 9')).toBeTruthy();
    });
  });

  // 7. GAD-7 renders first item text
  it('renders the first GAD-7 item text', () => {
    render(<TestRoot instrumentId="gad7" />);
    expect(
      screen.getByText('Feeling nervous, anxious, or on edge'),
    ).toBeTruthy();
  });

  // 8. WHO-5 renders first item text
  it('renders the first WHO-5 item text', () => {
    render(<TestRoot instrumentId="who5" />);
    expect(screen.getByText('I have felt cheerful and in good spirits')).toBeTruthy();
  });

  // 9. WHO-5 shows "At no time" response option
  it('WHO-5 shows "At no time" as first response option', () => {
    render(<TestRoot instrumentId="who5" />);
    expect(screen.getByLabelText('At no time')).toBeTruthy();
  });

  // 10. PHQ-9 item 9: safety message when value > 0
  it('shows safety message after answering item 9 with value > 0', async () => {
    render(<TestRoot instrumentId="phq9" />);

    // Answer questions 1–8 with "Not at all" (0)
    for (let q = 0; q < 8; q++) {
      // Select "Not at all"
      fireEvent.press(screen.getByLabelText('Not at all'));
      await waitFor(() => {
        const nextBtn = screen.getByLabelText('Next question');
        expect(nextBtn.props.accessibilityState?.disabled).toBe(false);
      });
      fireEvent.press(screen.getByLabelText('Next question'));
    }

    // Now on question 9 (index 8)
    await waitFor(() => {
      expect(screen.getByText('9 / 9')).toBeTruthy();
    });

    // Select "Several days" (value = 1 — triggers safety flag)
    fireEvent.press(screen.getByLabelText('Several days'));
    await waitFor(() => {
      const submitBtn = screen.getByLabelText('Submit assessment');
      expect(submitBtn.props.accessibilityState?.disabled).toBe(false);
    });

    fireEvent.press(screen.getByLabelText('Submit assessment'));

    await waitFor(() => {
      expect(
        screen.getByText(
          /You mentioned thoughts of self-harm\. You're not alone\./,
        ),
      ).toBeTruthy();
    });
  });

  // 11. Safety card "Get support now" button navigates to Crisis
  it('"Get support now" navigates to the Crisis screen', async () => {
    render(<TestRoot instrumentId="phq9" />);

    // Answer questions 1–8 with value 0
    for (let q = 0; q < 8; q++) {
      fireEvent.press(screen.getByLabelText('Not at all'));
      await waitFor(() => {
        expect(
          screen.getByLabelText('Next question').props.accessibilityState?.disabled,
        ).toBe(false);
      });
      fireEvent.press(screen.getByLabelText('Next question'));
    }

    // Answer item 9 with a flagged value
    await waitFor(() => {
      expect(screen.getByText('9 / 9')).toBeTruthy();
    });
    fireEvent.press(screen.getByLabelText('Several days'));
    await waitFor(() => {
      expect(
        screen.getByLabelText('Submit assessment').props.accessibilityState?.disabled,
      ).toBe(false);
    });
    fireEvent.press(screen.getByLabelText('Submit assessment'));

    await waitFor(() => {
      expect(screen.getByLabelText('Get crisis support now')).toBeTruthy();
    });

    fireEvent.press(screen.getByLabelText('Get crisis support now'));

    // Should navigate to Crisis screen
    await waitFor(() => {
      expect(screen.getByText("You're here. That matters.")).toBeTruthy();
    });
  });

  // 12. PHQ-9 item 9 = 0 does NOT show safety message
  it('does NOT show safety message when PHQ-9 item 9 = 0', async () => {
    render(<TestRoot instrumentId="phq9" />);

    // Answer all 9 questions with "Not at all" (0)
    for (let q = 0; q < 8; q++) {
      fireEvent.press(screen.getByLabelText('Not at all'));
      await waitFor(() => {
        expect(
          screen.getByLabelText('Next question').props.accessibilityState?.disabled,
        ).toBe(false);
      });
      fireEvent.press(screen.getByLabelText('Next question'));
    }

    await waitFor(() => {
      expect(screen.getByText('9 / 9')).toBeTruthy();
    });
    fireEvent.press(screen.getByLabelText('Not at all'));
    await waitFor(() => {
      expect(
        screen.getByLabelText('Submit assessment').props.accessibilityState?.disabled,
      ).toBe(false);
    });
    fireEvent.press(screen.getByLabelText('Submit assessment'));

    await waitFor(() => {
      expect(
        screen.getByText(/Thank you for completing this assessment/),
      ).toBeTruthy();
    });

    expect(
      screen.queryByText(/You mentioned thoughts of self-harm/),
    ).toBeNull();
  });

  // 13. Completion screen shows score in Latin digits
  it('completion screen renders score as Latin digits', async () => {
    render(<TestRoot instrumentId="phq9" />);

    // Answer all 9 with "Not at all"
    for (let q = 0; q < 8; q++) {
      fireEvent.press(screen.getByLabelText('Not at all'));
      await waitFor(() => {
        expect(
          screen.getByLabelText('Next question').props.accessibilityState?.disabled,
        ).toBe(false);
      });
      fireEvent.press(screen.getByLabelText('Next question'));
    }
    await waitFor(() => expect(screen.getByText('9 / 9')).toBeTruthy());
    fireEvent.press(screen.getByLabelText('Not at all'));
    await waitFor(() => {
      expect(
        screen.getByLabelText('Submit assessment').props.accessibilityState?.disabled,
      ).toBe(false);
    });
    fireEvent.press(screen.getByLabelText('Submit assessment'));

    await waitFor(() => {
      // Score 0 — all zeros
      const scoreEl = screen.getByText('0');
      // Latin digit '0' is ASCII — verify no non-ASCII chars
      expect(/^\d+$/.test(scoreEl.props.children)).toBe(true);
    });
  });

  // 14. Last question shows "Submit" not "Next"
  it('last question shows "Submit" button label', async () => {
    render(<TestRoot instrumentId="who5" />);

    // Answer questions 1–4 (indices 0–3)
    for (let q = 0; q < 4; q++) {
      fireEvent.press(screen.getByLabelText('At no time'));
      await waitFor(() => {
        expect(
          screen.getByLabelText('Next question').props.accessibilityState?.disabled,
        ).toBe(false);
      });
      fireEvent.press(screen.getByLabelText('Next question'));
    }

    // Now on question 5 (index 4) — should show "Submit"
    await waitFor(() => {
      expect(screen.getByText('5 / 5')).toBeTruthy();
    });
    expect(screen.queryByLabelText('Submit assessment')).toBeTruthy();
    expect(screen.queryByLabelText('Next question')).toBeNull();
  });
});
