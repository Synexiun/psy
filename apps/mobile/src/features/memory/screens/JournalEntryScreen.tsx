import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { color, radius, size, space } from '@theme/tokens';
import { useMemory } from '@features/memory/store';
import type { RootStackParamList } from '@app/App';

export function JournalEntryScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const addEntry = useMemory((s) => s.addEntry);
  const [body, setBody] = useState('');

  const now = new Date();
  // Latin locale for date rendering (CLAUDE.md rule 9 — Latin digits for clinical/data values;
  // journal dates are not clinical scores but we keep them locale-neutral for consistency).
  const dateLabel = now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const handleSave = () => {
    const trimmed = body.trim();
    if (trimmed.length === 0) {
      navigation.goBack();
      return;
    }
    addEntry(trimmed);
    navigation.goBack();
  };

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Top bar */}
      <View style={styles.topBar}>
        <View style={styles.topBarLeft}>
          <Text style={styles.topBarTitle}>New entry</Text>
          <Text style={styles.topBarDate}>{dateLabel}</Text>
        </View>

        <Pressable
          style={[styles.saveButton, body.trim().length === 0 && styles.saveButtonDisabled]}
          onPress={handleSave}
          accessibilityRole="button"
          accessibilityLabel="Save journal entry"
          accessibilityState={{ disabled: body.trim().length === 0 }}
        >
          <Text
            style={[
              styles.saveButtonText,
              body.trim().length === 0 && styles.saveButtonTextDisabled,
            ]}
          >
            Save
          </Text>
        </Pressable>
      </View>

      {/* Text editor */}
      <TextInput
        style={styles.editor}
        multiline
        autoFocus
        value={body}
        onChangeText={setBody}
        placeholder="What's on your mind?"
        placeholderTextColor={color.slate}
        textAlignVertical="top"
        accessibilityLabel="Journal entry text"
        scrollEnabled
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: color.offWhite,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: space.lg,
    paddingHorizontal: space.lg,
    paddingBottom: space.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: color.mist,
  },
  topBarLeft: {
    flex: 1,
    gap: 2,
  },
  topBarTitle: {
    fontSize: size.subhead,
    color: color.graphite,
    fontWeight: '600',
  },
  topBarDate: {
    fontSize: size.caption,
    color: color.slate,
  },
  saveButton: {
    backgroundColor: color.signalBlue,
    borderRadius: radius.md,
    paddingVertical: space.sm,
    paddingHorizontal: space.md,
    minHeight: 44,
    minWidth: 72,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveButtonDisabled: {
    backgroundColor: color.mist,
  },
  saveButtonText: {
    fontSize: size.body,
    color: color.offWhite,
  },
  saveButtonTextDisabled: {
    color: color.slate,
  },
  editor: {
    flex: 1,
    paddingHorizontal: space.lg,
    paddingVertical: space.lg,
    fontSize: size.body,
    color: color.graphite,
    lineHeight: 26,
  },
});
