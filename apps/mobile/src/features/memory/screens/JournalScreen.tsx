import React from 'react';
import {
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { color, radius, size, space } from '@theme/tokens';
import { useMemory } from '@features/memory/store';
import type { JournalEntry } from '@features/memory/store';
import type { RootStackParamList } from '@app/App';

function EntryCard({ entry }: { entry: JournalEntry }) {
  const date = new Date(entry.createdAt);
  // Latin date format — no locale-specific digit rendering (CLAUDE.md rule 9).
  const dateLabel = date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
  const timeLabel = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

  return (
    <View style={styles.card} accessibilityRole="text">
      <View style={styles.cardMeta}>
        <Text style={styles.cardDate}>{dateLabel}</Text>
        <Text style={styles.cardTime}>{timeLabel}</Text>
      </View>
      <Text style={styles.cardBody} numberOfLines={4}>
        {entry.body}
      </Text>
    </View>
  );
}

function EmptyState() {
  return (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyTitle}>Your journal is private.</Text>
      <Text style={styles.emptyHint}>Start writing.</Text>
    </View>
  );
}

export function JournalScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const entries = useMemory((s) => s.entries);

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Journal</Text>
      </View>

      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <EntryCard entry={item} />}
        contentContainerStyle={[
          styles.list,
          entries.length === 0 && styles.listEmpty,
        ]}
        ListEmptyComponent={<EmptyState />}
        showsVerticalScrollIndicator={false}
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('JournalEntry')}
        activeOpacity={0.8}
        accessibilityRole="button"
        accessibilityLabel="New journal entry"
      >
        <Text style={styles.fabIcon}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const FAB_SIZE = 56;

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
  list: {
    paddingHorizontal: space.lg,
    gap: space.md,
    paddingBottom: FAB_SIZE + space.xl,
  },
  listEmpty: {
    flex: 1,
  },
  card: {
    backgroundColor: color.mist,
    borderRadius: radius.md,
    padding: space.lg,
    gap: space.sm,
  },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  cardDate: {
    fontSize: size.caption,
    color: color.graphite,
    fontWeight: '600',
  },
  cardTime: {
    fontSize: size.caption,
    color: color.slate,
  },
  cardBody: {
    fontSize: size.body,
    color: color.graphite,
    lineHeight: 22,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
    paddingHorizontal: space.xl,
  },
  emptyTitle: {
    fontSize: size.subhead,
    color: color.graphite,
    textAlign: 'center',
  },
  emptyHint: {
    fontSize: size.body,
    color: color.slate,
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    bottom: space.xl,
    right: space.lg,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: color.signalBlue,
    alignItems: 'center',
    justifyContent: 'center',
    // Shadow (iOS)
    shadowColor: color.graphite,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    // Elevation (Android)
    elevation: 6,
  },
  fabIcon: {
    fontSize: 28,
    color: color.offWhite,
    lineHeight: 32,
  },
});
