import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import type { RootStackParamList } from '@app/App';
import { color, radius, size, space } from '@theme/tokens';
import { useResilience } from '@features/resilience/store';
import { useTabSwitch } from '@components/TabSwitchContext';

/**
 * Stub pattern data — these will come from the pattern module once wired.
 * Hardcoded for Sprint 111 per task spec.
 */
const PATTERN_STUBS = [
  'Evening urges are 2× more frequent than mornings.',
  'Urges handled without acting: 8 in the last 7 days.',
  'Box breathing used 5 times — most used tool this week.',
] as const;

export function HomeScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { switchTab } = useTabSwitch();
  const { continuousDays, resilienceDays, urgesHandledTotal } = useResilience();

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Resilience streak ─────────────────────────────── */}
      <View style={styles.streakCard}>
        <Text style={styles.streakLabel}>Resilience</Text>
        <Text style={styles.streakValue}>{resilienceDays} days</Text>
        <Text style={styles.streakSubtle}>
          {urgesHandledTotal} urges handled · never resets
        </Text>
      </View>

      {/* ── Continuous streak ─────────────────────────────── */}
      <View style={styles.streakCard}>
        <Text style={styles.streakLabel}>Continuous</Text>
        <Text style={styles.streakValue}>{continuousDays} days</Text>
      </View>

      {/* ── Patterns ──────────────────────────────────────── */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent patterns</Text>
        {PATTERN_STUBS.map((p, i) => (
          <View key={i} style={styles.patternRow}>
            <View style={styles.patternDot} />
            <Text style={styles.patternText}>{p}</Text>
          </View>
        ))}
      </View>

      {/* ── Primary action ────────────────────────────────── */}
      <Pressable
        style={styles.primary}
        onPress={() => switchTab('CheckIn')}
        accessibilityRole="button"
        accessibilityLabel="Log an urge — open check-in"
      >
        <Text style={styles.primaryText}>Check in</Text>
      </Pressable>

      {/* ── Assessments quick-action ──────────────────────── */}
      <Pressable
        style={styles.secondary}
        onPress={() => navigation.navigate('AssessmentList')}
        accessibilityRole="button"
        accessibilityLabel="Take an assessment — PHQ-9, GAD-7, WHO-5"
      >
        <Text style={styles.secondaryText}>Assessments</Text>
      </Pressable>

      {/* ── Crisis / support ──────────────────────────────── */}
      <Pressable
        style={styles.sos}
        onPress={() => navigation.navigate('Crisis')}
        accessibilityRole="button"
        accessibilityLabel="Need help now — open crisis support tools"
      >
        <Text style={styles.sosText}>Need help now</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: color.offWhite,
  },
  container: {
    padding: space.lg,
    gap: space.md,
    paddingBottom: space.xl,
  },
  streakCard: {
    backgroundColor: color.mist,
    padding: space.lg,
    borderRadius: radius.lg,
  },
  streakLabel: {
    fontSize: size.caption,
    color: color.slate,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  streakValue: {
    fontSize: size.display,
    color: color.graphite,
    marginVertical: space.xs,
  },
  streakSubtle: {
    fontSize: size.caption,
    color: color.slate,
  },
  section: {
    gap: space.sm,
    marginTop: space.sm,
  },
  sectionTitle: {
    fontSize: size.subhead,
    color: color.graphite,
    fontWeight: '600',
    marginBottom: space.xs,
  },
  patternRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: space.sm,
  },
  patternDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: color.calm,
    marginTop: 8,
    flexShrink: 0,
  },
  patternText: {
    flex: 1,
    fontSize: size.body,
    color: color.slate,
    lineHeight: 22,
  },
  primary: {
    backgroundColor: color.signalBlue,
    padding: space.lg,
    borderRadius: radius.lg,
    alignItems: 'center',
    marginTop: space.sm,
    minHeight: 56,
    justifyContent: 'center',
  },
  primaryText: {
    color: color.offWhite,
    fontSize: size.subhead,
  },
  secondary: {
    backgroundColor: color.mist,
    padding: space.lg,
    borderRadius: radius.lg,
    alignItems: 'center',
    minHeight: 56,
    justifyContent: 'center',
  },
  secondaryText: {
    color: color.graphite,
    fontSize: size.subhead,
  },
  sos: {
    backgroundColor: color.graphite,
    padding: space.lg,
    borderRadius: radius.lg,
    alignItems: 'center',
    minHeight: 56,
    justifyContent: 'center',
  },
  sosText: {
    color: color.offWhite,
    fontSize: size.subhead,
  },
});
