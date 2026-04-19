import { useEffect } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { color, size, space } from '@theme/tokens';

/**
 * T3 crisis flow — deterministic.
 *
 * Non-negotiable rules (see Docs/Technicals/06_ML_AI_Architecture.md §9.2):
 *  - Never calls the LLM.
 *  - Never awaits a network round-trip before rendering.
 *  - Never animates (reduces cognitive load).
 *  - Never shows a confirmation dialog.
 *  - Never uses red/alarm colors.
 */
export function CrisisScreen() {
  useEffect(() => {
    // Fire-and-forget network notification; no await, no dependency.
    // TODO: wire crisisClient.postSOS() when API client is available.
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>You're here. That matters.</Text>

      <View style={styles.toolList}>
        <Pressable style={styles.tool} accessibilityLabel="Start urge surf">
          <Text style={styles.toolText}>Urge surf · 5 min</Text>
        </Pressable>
        <Pressable style={styles.tool} accessibilityLabel="Start TIPP">
          <Text style={styles.toolText}>TIPP · 60 sec</Text>
        </Pressable>
        <Pressable style={styles.tool} accessibilityLabel="Call support contact">
          <Text style={styles.toolText}>Call Alex</Text>
        </Pressable>
      </View>

      <Text style={styles.hotline} accessibilityLabel="Crisis hotline 988">
        If you need more, 988 is there. Tap to dial.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: color.offWhite,
    padding: space.xl,
    justifyContent: 'center',
  },
  heading: {
    fontSize: size.display,
    color: color.graphite,
    marginBottom: space.xxl,
  },
  toolList: {
    gap: space.md,
  },
  tool: {
    backgroundColor: color.mist,
    borderRadius: 16,
    paddingVertical: space.lg,
    paddingHorizontal: space.xl,
    minHeight: 64,
    justifyContent: 'center',
  },
  toolText: {
    fontSize: size.crisis,
    color: color.graphite,
  },
  hotline: {
    fontSize: size.body,
    color: color.slate,
    marginTop: space.xxl,
  },
});
