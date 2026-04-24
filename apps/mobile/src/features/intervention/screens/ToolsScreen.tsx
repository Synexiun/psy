import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { color, radius, size, space } from '@theme/tokens';
import { TOOLS } from '@features/intervention/data/tools';
import type { RootStackParamList } from '@app/App';

/** Category → subtle background accent. Keeps cards scannable without color overload. */
const CATEGORY_ACCENT: Record<string, string> = {
  Breathing: '#D1FAE5',   // soft green
  Grounding: '#E0F2FE',   // soft sky
  Body: '#FCE7F3',         // soft pink
  Mindfulness: '#EDE9FE', // soft violet
  Behavioural: '#FEF3C7', // soft amber
};

export function ToolsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Coping Tools</Text>
        <Text style={styles.headerSubtitle}>All available offline.</Text>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      >
        {TOOLS.map((tool) => (
          <TouchableOpacity
            key={tool.toolId}
            style={styles.card}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel={`${tool.name}, ${tool.durationMinutes} minutes, ${tool.category}`}
            onPress={() =>
              navigation.navigate('ToolDetail', { toolId: tool.toolId })
            }
          >
            <View style={styles.cardTop}>
              <Text style={styles.toolName}>{tool.name}</Text>
              <Text style={styles.toolTagline}>{tool.tagline}</Text>
            </View>

            <View style={styles.badgeRow}>
              <View style={styles.durationBadge}>
                <Text style={styles.durationText}>
                  {tool.durationMinutes} min
                </Text>
              </View>
              <View
                style={[
                  styles.categoryBadge,
                  {
                    backgroundColor:
                      CATEGORY_ACCENT[tool.category] ?? color.mist,
                  },
                ]}
              >
                <Text style={styles.categoryText}>{tool.category}</Text>
              </View>
            </View>
          </TouchableOpacity>
        ))}

        {/* Bottom padding so last card clears the tab bar */}
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
    paddingTop: space.lg,
    paddingHorizontal: space.lg,
    paddingBottom: space.md,
  },
  headerTitle: {
    fontSize: size.title,
    color: color.graphite,
  },
  headerSubtitle: {
    fontSize: size.caption,
    color: color.slate,
    marginTop: space.xs,
  },
  scroll: {
    flex: 1,
  },
  list: {
    paddingHorizontal: space.lg,
    gap: space.md,
  },
  card: {
    backgroundColor: color.mist,
    borderRadius: radius.md,
    padding: space.lg,
    gap: space.sm,
  },
  cardTop: {
    gap: space.xs,
  },
  toolName: {
    fontSize: size.subhead,
    color: color.graphite,
    fontWeight: '600',
  },
  toolTagline: {
    fontSize: size.body,
    color: color.slate,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: space.sm,
    marginTop: space.xs,
  },
  durationBadge: {
    backgroundColor: color.offWhite,
    borderRadius: radius.pill,
    paddingHorizontal: space.sm,
    paddingVertical: 3,
  },
  durationText: {
    fontSize: size.caption,
    color: color.graphite,
  },
  categoryBadge: {
    borderRadius: radius.pill,
    paddingHorizontal: space.sm,
    paddingVertical: 3,
  },
  categoryText: {
    fontSize: size.caption,
    color: color.graphite,
  },
  bottomSpacer: {
    height: space.xl,
  },
});
