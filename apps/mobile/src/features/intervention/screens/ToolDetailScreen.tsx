import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { color, radius, size, space } from '@theme/tokens';
import { getToolById } from '@features/intervention/data/tools';
import { useIntervention } from '@features/intervention/store';
import type { RootStackParamList } from '@app/App';

// ---------------------------------------------------------------------------
// Box Breathing constants (4-4-4-4)
// ---------------------------------------------------------------------------
const PHASE_DURATION_MS = 4_000;

type BreathPhase = 'Inhale' | 'Hold' | 'Exhale' | 'Rest';

const PHASES: BreathPhase[] = ['Inhale', 'Hold', 'Exhale', 'Rest'];

const PHASE_GUIDANCE: Record<BreathPhase, string> = {
  Inhale: 'Breathe in slowly through your nose.',
  Hold: 'Hold gently — no strain.',
  Exhale: 'Breathe out through your mouth.',
  Rest: 'Rest. Empty and still.',
};

// ---------------------------------------------------------------------------
// BoxBreathingGuide
// ---------------------------------------------------------------------------
function BoxBreathingGuide({ onDone }: { onDone: () => void }) {
  const [phaseIndex, setPhaseIndex] = useState(0);
  const scale = useRef(new Animated.Value(0.6)).current;
  const animRef = useRef<Animated.CompositeAnimation | null>(null);

  const currentPhase = PHASES[phaseIndex % PHASES.length] as BreathPhase;

  // Target scale: expand on inhale, stay large on hold, shrink on exhale, stay small on rest.
  const phaseTargetScale: Record<BreathPhase, number> = {
    Inhale: 1.0,
    Hold: 1.0,
    Exhale: 0.6,
    Rest: 0.6,
  };

  const runPhase = useCallback(
    (idx: number) => {
      const phase = PHASES[idx % PHASES.length] as BreathPhase;
      const toValue = phaseTargetScale[phase];

      animRef.current = Animated.timing(scale, {
        toValue,
        duration: PHASE_DURATION_MS,
        easing: Easing.inOut(Easing.ease),
        useNativeDriver: true,
      });

      animRef.current.start(({ finished }) => {
        if (finished) {
          setPhaseIndex((prev) => prev + 1);
        }
      });
    },
    // phaseTargetScale is a constant object; scale ref is stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [scale],
  );

  useEffect(() => {
    runPhase(phaseIndex);
    return () => {
      animRef.current?.stop();
    };
    // phaseIndex drives re-subscription; runPhase is stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phaseIndex]);

  return (
    <View style={breathStyles.container}>
      <Text style={breathStyles.phaseLabel}>{currentPhase}</Text>

      <View style={breathStyles.circleWrapper}>
        <Animated.View
          style={[breathStyles.circle, { transform: [{ scale }] }]}
          accessibilityLabel={`Breathing circle — ${currentPhase}`}
        />
      </View>

      <Text style={breathStyles.guidance}>{PHASE_GUIDANCE[currentPhase]}</Text>

      <Pressable
        style={breathStyles.doneButton}
        onPress={onDone}
        accessibilityRole="button"
        accessibilityLabel="Finish breathing exercise"
      >
        <Text style={breathStyles.doneText}>Done</Text>
      </Pressable>
    </View>
  );
}

const CIRCLE_MAX = 200;

const breathStyles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: space.xl,
    gap: space.xl,
    backgroundColor: color.offWhite,
  },
  phaseLabel: {
    fontSize: size.display,
    color: color.graphite,
    letterSpacing: 1,
  },
  circleWrapper: {
    width: CIRCLE_MAX,
    height: CIRCLE_MAX,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circle: {
    width: CIRCLE_MAX,
    height: CIRCLE_MAX,
    borderRadius: CIRCLE_MAX / 2,
    backgroundColor: color.calm,
    opacity: 0.75,
  },
  guidance: {
    fontSize: size.body,
    color: color.slate,
    textAlign: 'center',
  },
  doneButton: {
    marginTop: space.lg,
    paddingVertical: space.md,
    paddingHorizontal: space.xl,
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    minWidth: 140,
    alignItems: 'center',
    minHeight: 44,
    justifyContent: 'center',
  },
  doneText: {
    fontSize: size.subhead,
    color: color.offWhite,
  },
});

// ---------------------------------------------------------------------------
// ToolDetailScreen
// ---------------------------------------------------------------------------
export function ToolDetailScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const route = useRoute<RouteProp<RootStackParamList, 'ToolDetail'>>();
  const { toolId } = route.params;

  const recordToolUsage = useIntervention((s) => s.recordToolUsage);
  const [used, setUsed] = useState(false);

  const tool = getToolById(toolId);

  const handleMarkUsed = useCallback(() => {
    recordToolUsage(toolId);
    setUsed(true);
  }, [recordToolUsage, toolId]);

  const handleDone = useCallback(() => {
    recordToolUsage(toolId);
    navigation.goBack();
  }, [navigation, recordToolUsage, toolId]);

  if (!tool) {
    // Defensive: unknown toolId — go back rather than crash.
    return (
      <View style={detailStyles.errorContainer}>
        <Text style={detailStyles.errorText}>Tool not found.</Text>
        <Pressable style={detailStyles.backButton} onPress={() => navigation.goBack()}>
          <Text style={detailStyles.backText}>Go back</Text>
        </Pressable>
      </View>
    );
  }

  if (tool.hasBreathingAnimation) {
    return <BoxBreathingGuide onDone={handleDone} />;
  }

  return (
    <View style={detailStyles.root}>
      {/* Header */}
      <View style={detailStyles.header}>
        <Pressable
          style={detailStyles.backTouchable}
          onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel="Go back"
        >
          <Text style={detailStyles.backArrow}>←</Text>
        </Pressable>
        <View style={detailStyles.headerMeta}>
          <Text style={detailStyles.headerTitle}>{tool.name}</Text>
          <Text style={detailStyles.headerMeta2}>
            {tool.durationMinutes} min · {tool.category}
          </Text>
        </View>
      </View>

      <ScrollView
        style={detailStyles.scroll}
        contentContainerStyle={detailStyles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={detailStyles.description}>{tool.fullDescription}</Text>

        <View style={detailStyles.stepsContainer}>
          <Text style={detailStyles.stepsHeader}>How to do it</Text>
          {tool.steps.map((step, i) => (
            <View key={i} style={detailStyles.stepRow}>
              <View style={detailStyles.stepBullet}>
                <Text style={detailStyles.stepBulletText}>{i + 1}</Text>
              </View>
              <Text style={detailStyles.stepText}>{step}</Text>
            </View>
          ))}
        </View>

        {/* Mark as used */}
        {used ? (
          <View style={detailStyles.usedBanner}>
            <Text style={detailStyles.usedBannerText}>
              Recorded. You showed up for yourself.
            </Text>
          </View>
        ) : (
          <Pressable
            style={detailStyles.primaryButton}
            onPress={handleMarkUsed}
            accessibilityRole="button"
            accessibilityLabel={`Mark ${tool.name} as used`}
          >
            <Text style={detailStyles.primaryButtonText}>Mark as used</Text>
          </Pressable>
        )}

        <View style={detailStyles.bottomSpacer} />
      </ScrollView>
    </View>
  );
}

const detailStyles = StyleSheet.create({
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
  headerMeta: {
    flex: 1,
  },
  headerTitle: {
    fontSize: size.title,
    color: color.graphite,
    fontWeight: '600',
  },
  headerMeta2: {
    fontSize: size.caption,
    color: color.slate,
    marginTop: 2,
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingHorizontal: space.lg,
    paddingBottom: space.xl,
    gap: space.lg,
  },
  description: {
    fontSize: size.body,
    color: color.slate,
    lineHeight: 24,
  },
  stepsContainer: {
    gap: space.md,
  },
  stepsHeader: {
    fontSize: size.subhead,
    color: color.graphite,
    fontWeight: '600',
  },
  stepRow: {
    flexDirection: 'row',
    gap: space.md,
    alignItems: 'flex-start',
  },
  stepBullet: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: color.mist,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: 2,
  },
  stepBulletText: {
    fontSize: size.caption,
    color: color.graphite,
    fontWeight: '600',
  },
  stepText: {
    flex: 1,
    fontSize: size.body,
    color: color.graphite,
    lineHeight: 24,
  },
  primaryButton: {
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    paddingVertical: space.md,
    alignItems: 'center',
    minHeight: 52,
    justifyContent: 'center',
  },
  primaryButtonText: {
    fontSize: size.subhead,
    color: color.offWhite,
  },
  usedBanner: {
    backgroundColor: '#D1FAE5',
    borderRadius: radius.md,
    padding: space.md,
    alignItems: 'center',
  },
  usedBannerText: {
    fontSize: size.body,
    color: '#065F46',
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
  backButton: {
    paddingVertical: space.md,
    paddingHorizontal: space.xl,
    backgroundColor: color.mist,
    borderRadius: radius.md,
    minHeight: 44,
    justifyContent: 'center',
  },
  backText: {
    fontSize: size.body,
    color: color.graphite,
  },
  bottomSpacer: {
    height: space.xl,
  },
});
