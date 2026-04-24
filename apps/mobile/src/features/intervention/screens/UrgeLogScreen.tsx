import { useRef, useState } from 'react';
import {
  AccessibilityInfo,
  PanResponder,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { color, font, radius, size, space } from '@theme/tokens';
import { useIntervention } from '../store';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NOTES_MAX_CHARS = 280;

type TriggerKey =
  | 'stress'
  | 'boredom'
  | 'socialPressure'
  | 'loneliness'
  | 'anger'
  | 'anxiety'
  | 'celebration'
  | 'fatigue';

const TRIGGER_KEYS: TriggerKey[] = [
  'stress',
  'boredom',
  'socialPressure',
  'loneliness',
  'anger',
  'anxiety',
  'celebration',
  'fatigue',
];

const TRIGGER_LABELS: Record<TriggerKey, string> = {
  stress: 'Stress',
  boredom: 'Boredom',
  socialPressure: 'Social pressure',
  loneliness: 'Loneliness',
  anger: 'Anger',
  anxiety: 'Anxiety',
  celebration: 'Celebration',
  fatigue: 'Fatigue',
};

// ---------------------------------------------------------------------------
// Intensity helpers — Latin-digit only, no locale formatting
// ---------------------------------------------------------------------------

/** Maps 0–10 to a theme colour string. Green ≤3, amber ≤6, red >6. */
function intensityColor(value: number): string {
  if (value <= 3) return color.calm;     // green-ish
  if (value <= 6) return color.elevated; // amber
  return color.crisis;                   // red
}

// ---------------------------------------------------------------------------
// IntensitySlider — built on PanResponder, no new native deps
// ---------------------------------------------------------------------------

interface IntensitySliderProps {
  value: number;
  onChange: (v: number) => void;
}

function IntensitySlider({ value, onChange }: IntensitySliderProps) {
  const trackWidth = useRef(0);

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        if (trackWidth.current === 0) return;
        const x = evt.nativeEvent.locationX;
        const clamped = Math.max(0, Math.min(x, trackWidth.current));
        const next = Math.round((clamped / trackWidth.current) * 10);
        onChange(next);
      },
      onPanResponderMove: (evt) => {
        if (trackWidth.current === 0) return;
        const x = evt.nativeEvent.locationX;
        const clamped = Math.max(0, Math.min(x, trackWidth.current));
        const next = Math.round((clamped / trackWidth.current) * 10);
        onChange(next);
      },
    }),
  ).current;

  const fillPercent = (value / 10) * 100;
  const activeColor = intensityColor(value);

  return (
    <View style={sliderStyles.wrapper}>
      {/* Track hit area */}
      <View
        style={sliderStyles.trackHitArea}
        onLayout={(e) => {
          trackWidth.current = e.nativeEvent.layout.width;
        }}
        {...panResponder.panHandlers}
        accessible
        accessibilityRole="adjustable"
        accessibilityLabel="Urge intensity"
        accessibilityValue={{ min: 0, max: 10, now: value }}
        onAccessibilityAction={(e) => {
          if (e.nativeEvent.actionName === 'increment') {
            onChange(Math.min(10, value + 1));
          } else if (e.nativeEvent.actionName === 'decrement') {
            onChange(Math.max(0, value - 1));
          }
        }}
        accessibilityActions={[
          { name: 'increment' },
          { name: 'decrement' },
        ]}
      >
        {/* Background track */}
        <View style={sliderStyles.trackBg} />
        {/* Filled portion */}
        <View
          style={[
            sliderStyles.trackFill,
            { width: `${fillPercent}%` as unknown as number, backgroundColor: activeColor },
          ]}
        />
        {/* Thumb */}
        <View
          style={[
            sliderStyles.thumb,
            {
              left: `${fillPercent}%` as unknown as number,
              backgroundColor: activeColor,
            },
          ]}
        />
      </View>

      {/* Labels row: 0 — large digit — 10 */}
      <View style={sliderStyles.labelsRow}>
        <Text style={sliderStyles.scaleLabel}>0</Text>
        <Text style={[sliderStyles.intensityDisplay, { color: activeColor }]}>
          {value.toString()}
        </Text>
        <Text style={sliderStyles.scaleLabel}>10</Text>
      </View>

      {/* Step dots for quick tap */}
      <View style={sliderStyles.dotsRow}>
        {Array.from({ length: 11 }, (_, i) => (
          <TouchableOpacity
            key={i}
            onPress={() => onChange(i)}
            style={[
              sliderStyles.dot,
              {
                backgroundColor:
                  i <= value ? activeColor : color.mist,
                borderColor: i === value ? activeColor : 'transparent',
              },
            ]}
            accessibilityLabel={i.toString()}
          />
        ))}
      </View>
    </View>
  );
}

const sliderStyles = StyleSheet.create({
  wrapper: {
    gap: space.sm,
  },
  trackHitArea: {
    height: 40,
    justifyContent: 'center',
    position: 'relative',
  },
  trackBg: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: color.mist,
  },
  trackFill: {
    position: 'absolute',
    left: 0,
    height: 8,
    borderRadius: radius.pill,
  },
  thumb: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderRadius: radius.pill,
    marginLeft: -12,
    top: '50%',
    marginTop: -12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.18,
    shadowRadius: 3,
    elevation: 3,
  },
  labelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scaleLabel: {
    fontSize: size.caption,
    color: color.slate,
    fontFamily: font.body,
  },
  intensityDisplay: {
    fontSize: 40,
    fontFamily: font.display,
    fontWeight: '700',
    lineHeight: 48,
    textAlign: 'center',
    minWidth: 56,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 4,
  },
  dot: {
    width: 18,
    height: 18,
    borderRadius: radius.pill,
    borderWidth: 2,
  },
});

// ---------------------------------------------------------------------------
// TriggerChip
// ---------------------------------------------------------------------------

interface TriggerChipProps {
  label: string;
  selected: boolean;
  onPress: () => void;
}

function TriggerChip({ label, selected, onPress }: TriggerChipProps) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[chipStyles.chip, selected && chipStyles.chipSelected]}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: selected }}
      accessibilityLabel={label}
      activeOpacity={0.75}
    >
      <Text style={[chipStyles.label, selected && chipStyles.labelSelected]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const chipStyles = StyleSheet.create({
  chip: {
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    borderRadius: radius.pill,
    backgroundColor: color.mist,
    borderWidth: 1.5,
    borderColor: color.mist,
    marginBottom: space.sm,
    marginRight: space.sm,
  },
  chipSelected: {
    backgroundColor: color.signalBlue,
    borderColor: color.signalBlue,
  },
  label: {
    fontSize: size.body,
    color: color.graphite,
    fontFamily: font.body,
  },
  labelSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
});

// ---------------------------------------------------------------------------
// SuccessCard — compassion-first
// ---------------------------------------------------------------------------

interface SuccessCardProps {
  onReset: () => void;
}

function SuccessCard({ onReset }: SuccessCardProps) {
  return (
    <View style={successStyles.card}>
      <Text style={successStyles.wave} aria-hidden>{'🌊'}</Text>
      <Text style={successStyles.headline}>
        Noticing it is the first move.
      </Text>
      <Text style={successStyles.body}>
        This is already resilience. You paused before acting — that pause is
        the whole skill.
      </Text>
      <TouchableOpacity
        onPress={onReset}
        style={successStyles.button}
        accessibilityRole="button"
        activeOpacity={0.8}
      >
        <Text style={successStyles.buttonLabel}>Log another</Text>
      </TouchableOpacity>
    </View>
  );
}

const successStyles = StyleSheet.create({
  card: {
    backgroundColor: color.offWhite,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: color.mist,
    padding: space.xl,
    alignItems: 'center',
    gap: space.md,
    marginTop: space.lg,
  },
  wave: {
    fontSize: 48,
  },
  headline: {
    fontSize: size.title,
    fontFamily: font.display,
    fontWeight: '600',
    color: color.graphite,
    textAlign: 'center',
  },
  body: {
    fontSize: size.body,
    fontFamily: font.body,
    color: color.slate,
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: 280,
  },
  button: {
    marginTop: space.sm,
    paddingVertical: space.sm,
    paddingHorizontal: space.lg,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    borderColor: color.slate,
  },
  buttonLabel: {
    fontSize: size.body,
    fontFamily: font.body,
    color: color.slate,
  },
});

// ---------------------------------------------------------------------------
// UrgeLogScreen — main export
// ---------------------------------------------------------------------------

export function UrgeLogScreen() {
  const { recordUrgeCheckIn } = useIntervention();

  const [intensity, setIntensity] = useState(0);
  const [selectedTriggers, setSelectedTriggers] = useState<Set<TriggerKey>>(new Set());
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function toggleTrigger(key: TriggerKey) {
    setSelectedTriggers((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  function handleSubmit() {
    if (intensity === 0 || isSubmitting) return;
    setIsSubmitting(true);
    recordUrgeCheckIn(intensity, Array.from(selectedTriggers), notes);
    setIsSubmitting(false);
    setSubmitted(true);
  }

  function handleReset() {
    setIntensity(0);
    setSelectedTriggers(new Set());
    setNotes('');
    setSubmitted(false);
  }

  const charsLeft = NOTES_MAX_CHARS - notes.length;
  const canSubmit = intensity > 0 && !isSubmitting;

  if (submitted) {
    return (
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.contentContainer}
        keyboardShouldPersistTaps="handled"
      >
        <SuccessCard onReset={handleReset} />
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.contentContainer}
      keyboardShouldPersistTaps="handled"
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Log an urge</Text>
        <Text style={styles.subtitle}>
          Noticing it is already a move. Keep it short — intensity first.
        </Text>
      </View>

      {/* Intensity section */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>How strong is the urge?</Text>
        <IntensitySlider value={intensity} onChange={setIntensity} />
      </View>

      {/* Trigger chips section */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>What triggered it? (optional)</Text>
        <View style={styles.chipsRow}>
          {TRIGGER_KEYS.map((key) => (
            <TriggerChip
              key={key}
              label={TRIGGER_LABELS[key]}
              selected={selectedTriggers.has(key)}
              onPress={() => toggleTrigger(key)}
            />
          ))}
        </View>
      </View>

      {/* Notes section */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>Notes (optional)</Text>
        <TextInput
          style={styles.textInput}
          value={notes}
          onChangeText={(text) => {
            if (text.length <= NOTES_MAX_CHARS) {
              setNotes(text);
            }
          }}
          placeholder="Anything you want to remember about this moment…"
          placeholderTextColor={color.slate}
          multiline
          maxLength={NOTES_MAX_CHARS}
          returnKeyType="done"
          blurOnSubmit
          accessibilityLabel="Notes"
          accessibilityHint={`Maximum ${NOTES_MAX_CHARS.toString()} characters`}
        />
        <Text
          style={[
            styles.charCount,
            charsLeft < 30 && styles.charCountWarning,
          ]}
          accessibilityLiveRegion="polite"
        >
          {charsLeft.toString()} chars left
        </Text>
      </View>

      {/* Submit button */}
      <TouchableOpacity
        style={[styles.submitButton, !canSubmit && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={!canSubmit}
        accessibilityRole="button"
        accessibilityState={{ disabled: !canSubmit }}
        accessibilityLabel={isSubmitting ? 'Saving…' : 'Log this urge'}
        activeOpacity={0.85}
      >
        <Text style={[styles.submitLabel, !canSubmit && styles.submitLabelDisabled]}>
          {isSubmitting ? 'Saving…' : 'Log this urge'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: color.offWhite,
  },
  contentContainer: {
    padding: space.lg,
    paddingBottom: space.xxl,
    gap: space.lg,
  },
  header: {
    gap: space.xs,
  },
  title: {
    fontSize: size.display,
    fontFamily: font.display,
    fontWeight: '700',
    color: color.graphite,
  },
  subtitle: {
    fontSize: size.body,
    fontFamily: font.body,
    color: color.slate,
    lineHeight: 22,
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: color.mist,
    padding: space.md,
    gap: space.sm,
  },
  sectionLabel: {
    fontSize: size.body,
    fontFamily: font.body,
    fontWeight: '600',
    color: color.graphite,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  textInput: {
    fontSize: size.body,
    fontFamily: font.body,
    color: color.graphite,
    backgroundColor: color.offWhite,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: color.mist,
    padding: space.sm,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: size.caption,
    fontFamily: font.body,
    color: color.slate,
    textAlign: 'right',
  },
  charCountWarning: {
    color: color.elevated,
  },
  submitButton: {
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    paddingVertical: space.md,
    alignItems: 'center',
    marginTop: space.xs,
  },
  submitButtonDisabled: {
    backgroundColor: color.mist,
  },
  submitLabel: {
    fontSize: size.subhead,
    fontFamily: font.body,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  submitLabelDisabled: {
    color: color.slate,
  },
});
