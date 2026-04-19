import { StyleSheet, Text, View } from 'react-native';

import { color, size, space } from '@theme/tokens';

export function UrgeLogScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Log an urge</Text>
      <Text style={styles.hint}>
        Noticing it is already a move. Keep it short — intensity first, trigger tags later.
      </Text>
      {/* TODO: intensity slider, trigger chips, submit. */}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: color.offWhite,
    padding: space.lg,
  },
  title: {
    fontSize: size.title,
    color: color.graphite,
    marginBottom: space.sm,
  },
  hint: {
    fontSize: size.body,
    color: color.slate,
  },
});
