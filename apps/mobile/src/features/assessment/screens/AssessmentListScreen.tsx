/**
 * AssessmentListScreen — shows available assessments for the current user.
 *
 * Accessed from the HomeScreen "Assessments" quick-action or any future
 * in-app deep link. Not in the main tab bar.
 *
 * Design notes:
 * - Each card shows the instrument name, last score (if any), estimated time,
 *   and a "Take now" button that pushes AssessmentSession.
 * - Last scores persist via the assessment Zustand store (MMKV-backed).
 * - Scores are always rendered in Latin digits (CLAUDE.md rule 9).
 */

import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import type { RootStackParamList } from '@app/App';
import { color, radius, size, space } from '@theme/tokens';
import { useAssessment, INSTRUMENTS } from '@features/assessment/store';
import type { InstrumentId } from '@features/assessment/store';

// ---------------------------------------------------------------------------
// Displayed instrument list — ordered by clinical priority
// ---------------------------------------------------------------------------
const ASSESSMENT_LIST: InstrumentId[] = ['phq9', 'gad7', 'who5'];

export function AssessmentListScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { lastScores, startInstrument } = useAssessment();

  const handleTakeNow = (id: InstrumentId) => {
    startInstrument(id);
    navigation.navigate('AssessmentSession', { instrumentId: id });
  };

  return (
    <View style={styles.root}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable
          style={styles.backTouchable}
          onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel="Go back"
        >
          <Text style={styles.backArrow}>←</Text>
        </Pressable>
        <Text style={styles.title}>Assessments</Text>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.intro}>
          Validated check-ins to track your mental well-being over time. Results
          are private and never shared without your consent.
        </Text>

        {ASSESSMENT_LIST.map((id) => {
          const instrument = INSTRUMENTS[id];
          const last = lastScores[id];

          return (
            <View key={id} style={styles.card}>
              <View style={styles.cardHeader}>
                <View style={styles.cardMeta}>
                  <Text style={styles.instrumentName}>{instrument.name}</Text>
                  <Text style={styles.instrumentFull}>{instrument.fullName}</Text>
                </View>
                <Text style={styles.time}>
                  ~{instrument.estimatedMinutes} min
                </Text>
              </View>

              {last != null ? (
                <View style={styles.lastScore}>
                  <Text style={styles.lastScoreLabel}>Last score</Text>
                  <Text style={styles.lastScoreValue}>
                    {/* Latin digits enforced by displayScoreString (CLAUDE.md rule 9) */}
                    {last.displayScoreString}
                    {'  '}
                    <Text style={styles.lastSeverity}>{last.severityLabel}</Text>
                  </Text>
                  <Text style={styles.lastDate}>
                    {new Date(last.completedAt).toLocaleDateString('en', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </Text>
                </View>
              ) : (
                <Text style={styles.noScore}>No previous score</Text>
              )}

              <Pressable
                style={styles.takeButton}
                onPress={() => handleTakeNow(id)}
                accessibilityRole="button"
                accessibilityLabel={`Take ${instrument.name} assessment now`}
              >
                <Text style={styles.takeButtonText}>Take now</Text>
              </Pressable>
            </View>
          );
        })}

        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerText}>
            These assessments are not a substitute for professional diagnosis.
            Scores are informational — one score isn't a diagnosis.
          </Text>
        </View>

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
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
  title: {
    fontSize: size.title,
    color: color.graphite,
    fontWeight: '600',
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingHorizontal: space.lg,
    paddingBottom: space.xl,
    gap: space.md,
  },
  intro: {
    fontSize: size.body,
    color: color.slate,
    lineHeight: 24,
    marginBottom: space.sm,
  },
  card: {
    backgroundColor: color.mist,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  cardMeta: {
    flex: 1,
    gap: 2,
  },
  instrumentName: {
    fontSize: size.subhead,
    color: color.graphite,
    fontWeight: '600',
  },
  instrumentFull: {
    fontSize: size.caption,
    color: color.slate,
  },
  time: {
    fontSize: size.caption,
    color: color.slate,
    flexShrink: 0,
    marginLeft: space.sm,
  },
  lastScore: {
    gap: 2,
    paddingTop: space.xs,
  },
  lastScoreLabel: {
    fontSize: size.caption,
    color: color.slate,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  lastScoreValue: {
    fontSize: size.title,
    color: color.graphite,
    fontWeight: '600',
  },
  lastSeverity: {
    fontSize: size.body,
    color: color.slate,
    fontWeight: '400',
  },
  lastDate: {
    fontSize: size.caption,
    color: color.slate,
  },
  noScore: {
    fontSize: size.body,
    color: color.slate,
    fontStyle: 'italic',
  },
  takeButton: {
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    paddingVertical: space.md,
    alignItems: 'center',
    minHeight: 48,
    justifyContent: 'center',
    marginTop: space.xs,
  },
  takeButtonText: {
    fontSize: size.subhead,
    color: color.offWhite,
  },
  disclaimer: {
    marginTop: space.sm,
    padding: space.md,
    backgroundColor: color.mist,
    borderRadius: radius.md,
  },
  disclaimerText: {
    fontSize: size.caption,
    color: color.slate,
    lineHeight: 18,
    textAlign: 'center',
  },
  bottomSpacer: {
    height: space.xl,
  },
});
