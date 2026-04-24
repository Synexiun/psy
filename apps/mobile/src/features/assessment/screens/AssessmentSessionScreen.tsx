/**
 * AssessmentSessionScreen — administers a single psychometric instrument.
 *
 * Flow:
 *   Question 1 → … → Question N → Completion view (inline)
 *
 * Clinical rules (12_Psychometric_System.md + CLAUDE.md):
 * - Item wording is verbatim — see INSTRUMENTS in store.ts.
 * - Scoring is deterministic, no LLM (rule 1 + §5.1).
 * - PHQ-9 item 9 safety flag: any response ≥ 1 shows compassionate safety
 *   message with a "Get support now" button navigating to 'Crisis' root screen.
 *   This path is never feature-flagged (rule 1 — T3/T4 flows are deterministic).
 * - Scores rendered in Latin digits (rule 9).
 * - Back navigation inside a session returns to the previous question; on
 *   question 1 it exits the session.
 */

import React, { useCallback, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import type { RootStackParamList } from '@app/App';
import { color, radius, size, space } from '@theme/tokens';
import {
  useAssessment,
  INSTRUMENTS,
  scoreInstrument,
} from '@features/assessment/store';
import type { InstrumentId, ScoringResult } from '@features/assessment/store';

// ---------------------------------------------------------------------------
// Progress bar
// ---------------------------------------------------------------------------
function ProgressBar({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
  const pct = total > 0 ? (current / total) * 100 : 0;
  return (
    <View style={progressStyles.track}>
      <View style={[progressStyles.fill, { width: `${pct}%` as any }]} />
    </View>
  );
}

const progressStyles = StyleSheet.create({
  track: {
    height: 4,
    backgroundColor: color.mist,
    borderRadius: radius.pill,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    backgroundColor: color.signalBlue,
    borderRadius: radius.pill,
  },
});

// ---------------------------------------------------------------------------
// Completion view (inline — no separate route)
// ---------------------------------------------------------------------------
interface CompletionViewProps {
  instrumentId: InstrumentId;
  result: ScoringResult;
  onDone: () => void;
  onCrisis: () => void;
}

function CompletionView({
  instrumentId,
  result,
  onDone,
  onCrisis,
}: CompletionViewProps) {
  const instrument = INSTRUMENTS[instrumentId];
  const isSafetyFlagged = result.safetyFlag;

  return (
    <ScrollView
      style={completionStyles.scroll}
      contentContainerStyle={completionStyles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={completionStyles.thanks}>
        Thank you for completing this assessment.
      </Text>

      <View style={completionStyles.scoreCard}>
        <Text style={completionStyles.instrumentName}>{instrument.name}</Text>
        {/* Latin digits — displayScoreString is always en-locale (CLAUDE.md rule 9) */}
        <Text style={completionStyles.scoreValue}>
          {result.displayScoreString}
        </Text>
        <Text style={completionStyles.severityLabel}>
          {result.severityLabel}
        </Text>
      </View>

      <Text style={completionStyles.compassion}>{result.compassionMessage}</Text>

      {/* PHQ-9 item 9 safety check — deterministic; never feature-flagged */}
      {isSafetyFlagged && (
        <View
          style={completionStyles.safetyCard}
          accessibilityRole="alert"
          accessibilityLabel="Safety support message"
        >
          <Text style={completionStyles.safetyText}>
            You mentioned thoughts of self-harm. You're not alone.{'\n'}
            Our crisis support is here for you.
          </Text>
          <Pressable
            style={completionStyles.safetyButton}
            onPress={onCrisis}
            accessibilityRole="button"
            accessibilityLabel="Get crisis support now"
          >
            <Text style={completionStyles.safetyButtonText}>
              Get support now
            </Text>
          </Pressable>
        </View>
      )}

      <Pressable
        style={completionStyles.doneButton}
        onPress={onDone}
        accessibilityRole="button"
        accessibilityLabel="Close assessment — done"
      >
        <Text style={completionStyles.doneButtonText}>Done</Text>
      </Pressable>

      <View style={completionStyles.bottomSpacer} />
    </ScrollView>
  );
}

const completionStyles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: color.offWhite,
  },
  content: {
    padding: space.lg,
    gap: space.lg,
  },
  thanks: {
    fontSize: size.title,
    color: color.graphite,
    fontWeight: '600',
    lineHeight: 32,
    marginTop: space.md,
  },
  scoreCard: {
    backgroundColor: color.mist,
    borderRadius: radius.lg,
    padding: space.lg,
    alignItems: 'center',
    gap: space.xs,
  },
  instrumentName: {
    fontSize: size.caption,
    color: color.slate,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  scoreValue: {
    fontSize: 48,
    color: color.graphite,
    fontWeight: '700',
    lineHeight: 56,
  },
  severityLabel: {
    fontSize: size.body,
    color: color.slate,
  },
  compassion: {
    fontSize: size.body,
    color: color.slate,
    lineHeight: 26,
  },
  safetyCard: {
    backgroundColor: '#FEF2F2',
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#FECACA',
    padding: space.lg,
    gap: space.md,
  },
  safetyText: {
    fontSize: size.body,
    color: '#991B1B',
    lineHeight: 26,
  },
  safetyButton: {
    backgroundColor: '#991B1B',
    borderRadius: radius.md,
    paddingVertical: space.md,
    alignItems: 'center',
    minHeight: 52,
    justifyContent: 'center',
  },
  safetyButtonText: {
    fontSize: size.subhead,
    color: '#FFF',
    fontWeight: '600',
  },
  doneButton: {
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    paddingVertical: space.md,
    alignItems: 'center',
    minHeight: 52,
    justifyContent: 'center',
  },
  doneButtonText: {
    fontSize: size.subhead,
    color: color.offWhite,
  },
  bottomSpacer: {
    height: space.xl,
  },
});

// ---------------------------------------------------------------------------
// AssessmentSessionScreen
// ---------------------------------------------------------------------------
export function AssessmentSessionScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const route =
    useRoute<RouteProp<RootStackParamList, 'AssessmentSession'>>();

  const { instrumentId } = route.params;
  const instrument = INSTRUMENTS[instrumentId];

  const { responses, setResponse, recordCompletion } = useAssessment();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [scoringResult, setScoringResult] = useState<ScoringResult | null>(null);

  const currentItem = instrument.items[currentIndex];
  const currentValue = responses[currentIndex] ?? null;
  const isLastQuestion = currentIndex === instrument.itemCount - 1;
  const showPreamble = currentIndex === 0 && instrument.preamble != null;

  const handleSelectOption = useCallback(
    (value: number) => {
      setResponse(currentIndex, value);
    },
    [currentIndex, setResponse],
  );

  const handleNext = useCallback(() => {
    if (isLastQuestion) {
      // Score and complete
      const result = scoreInstrument(instrumentId, {
        ...responses,
        [currentIndex]: currentValue!,
      });
      setScoringResult(result);
      recordCompletion({
        instrumentId,
        displayScore: result.displayScore,
        displayScoreString: result.displayScoreString,
        severityLabel: result.severityLabel,
        completedAt: new Date().toISOString(),
      });
      setCompleted(true);
    } else {
      setCurrentIndex((i) => i + 1);
    }
  }, [
    currentIndex,
    currentValue,
    instrumentId,
    isLastQuestion,
    recordCompletion,
    responses,
  ]);

  const handleBack = useCallback(() => {
    if (currentIndex === 0) {
      navigation.goBack();
    } else {
      setCurrentIndex((i) => i - 1);
    }
  }, [currentIndex, navigation]);

  const handleDone = useCallback(() => {
    navigation.goBack();
  }, [navigation]);

  const handleCrisis = useCallback(() => {
    // Crisis navigation is deterministic; no feature flag can alter this path.
    navigation.navigate('Crisis');
  }, [navigation]);

  // -- Completion view --
  if (completed && scoringResult != null) {
    return (
      <View style={sessionStyles.root}>
        <CompletionView
          instrumentId={instrumentId}
          result={scoringResult}
          onDone={handleDone}
          onCrisis={handleCrisis}
        />
      </View>
    );
  }

  // Guard: should not happen, but defend against undefined item
  if (currentItem == null) {
    return (
      <View style={sessionStyles.errorContainer}>
        <Text style={sessionStyles.errorText}>
          Something went wrong — question not found.
        </Text>
        <Pressable style={sessionStyles.errorBack} onPress={handleBack}>
          <Text style={sessionStyles.errorBackText}>Go back</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={sessionStyles.root}>
      {/* Header — back + progress */}
      <View style={sessionStyles.header}>
        <Pressable
          style={sessionStyles.backTouchable}
          onPress={handleBack}
          accessibilityRole="button"
          accessibilityLabel={
            currentIndex === 0
              ? 'Exit assessment'
              : 'Go to previous question'
          }
        >
          <Text style={sessionStyles.backArrow}>←</Text>
        </Pressable>
        <View style={sessionStyles.progressWrapper}>
          <ProgressBar current={currentIndex + 1} total={instrument.itemCount} />
          <Text style={sessionStyles.progressLabel}>
            {/* Latin digits for progress counter (CLAUDE.md rule 9) */}
            {(currentIndex + 1).toLocaleString('en')} /{' '}
            {instrument.itemCount.toLocaleString('en')}
          </Text>
        </View>
      </View>

      <ScrollView
        style={sessionStyles.scroll}
        contentContainerStyle={sessionStyles.content}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Preamble on first question */}
        {showPreamble && (
          <Text style={sessionStyles.preamble}>{instrument.preamble}</Text>
        )}

        {/* Question text */}
        <Text style={sessionStyles.questionText}>{currentItem.text}</Text>

        {/* Response options */}
        <View style={sessionStyles.optionsContainer}>
          {instrument.responseOptions.map((option) => {
            const isSelected = currentValue === option.value;
            return (
              <Pressable
                key={option.value}
                style={[
                  sessionStyles.option,
                  isSelected && sessionStyles.optionSelected,
                ]}
                onPress={() => handleSelectOption(option.value)}
                accessibilityRole="radio"
                accessibilityState={{ checked: isSelected }}
                accessibilityLabel={option.label}
              >
                <View
                  style={[
                    sessionStyles.radioOuter,
                    isSelected && sessionStyles.radioOuterSelected,
                  ]}
                >
                  {isSelected && <View style={sessionStyles.radioInner} />}
                </View>
                <Text
                  style={[
                    sessionStyles.optionText,
                    isSelected && sessionStyles.optionTextSelected,
                  ]}
                >
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      {/* Bottom action */}
      <View style={sessionStyles.footer}>
        <Pressable
          style={[
            sessionStyles.nextButton,
            currentValue === null && sessionStyles.nextButtonDisabled,
          ]}
          onPress={handleNext}
          disabled={currentValue === null}
          accessibilityRole="button"
          accessibilityLabel={isLastQuestion ? 'Submit assessment' : 'Next question'}
          accessibilityState={{ disabled: currentValue === null }}
        >
          <Text
            style={[
              sessionStyles.nextButtonText,
              currentValue === null && sessionStyles.nextButtonTextDisabled,
            ]}
          >
            {isLastQuestion ? 'Submit' : 'Next'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const sessionStyles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: color.offWhite,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: space.lg,
    paddingHorizontal: space.lg,
    paddingBottom: space.md,
    gap: space.md,
  },
  backTouchable: {
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backArrow: {
    fontSize: size.title,
    color: color.graphite,
  },
  progressWrapper: {
    flex: 1,
    gap: space.xs,
  },
  progressLabel: {
    fontSize: size.caption,
    color: color.slate,
    textAlign: 'right',
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingHorizontal: space.lg,
    paddingBottom: space.xl,
    gap: space.lg,
  },
  preamble: {
    fontSize: size.body,
    color: color.slate,
    lineHeight: 24,
    fontStyle: 'italic',
    paddingTop: space.sm,
  },
  questionText: {
    fontSize: size.title,
    color: color.graphite,
    lineHeight: 34,
    paddingTop: space.sm,
  },
  optionsContainer: {
    gap: space.sm,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    padding: space.md,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: color.mist,
    backgroundColor: color.offWhite,
    minHeight: 52,
  },
  optionSelected: {
    borderColor: color.signalBlue,
    backgroundColor: '#EEF2FF',
  },
  radioOuter: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: color.slate,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  radioOuterSelected: {
    borderColor: color.signalBlue,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: color.signalBlue,
  },
  optionText: {
    flex: 1,
    fontSize: size.body,
    color: color.graphite,
  },
  optionTextSelected: {
    color: color.signalBlue,
    fontWeight: '500',
  },
  footer: {
    padding: space.lg,
    paddingBottom: space.xl,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: color.mist,
    backgroundColor: color.offWhite,
  },
  nextButton: {
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    paddingVertical: space.md,
    alignItems: 'center',
    minHeight: 52,
    justifyContent: 'center',
  },
  nextButtonDisabled: {
    backgroundColor: color.mist,
  },
  nextButtonText: {
    fontSize: size.subhead,
    color: color.offWhite,
    fontWeight: '600',
  },
  nextButtonTextDisabled: {
    color: color.slate,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: space.xl,
    backgroundColor: color.offWhite,
    gap: space.lg,
  },
  errorText: {
    fontSize: size.body,
    color: color.slate,
  },
  errorBack: {
    paddingVertical: space.md,
    paddingHorizontal: space.xl,
    backgroundColor: color.mist,
    borderRadius: radius.md,
    minHeight: 44,
    justifyContent: 'center',
  },
  errorBackText: {
    fontSize: size.body,
    color: color.graphite,
  },
});
