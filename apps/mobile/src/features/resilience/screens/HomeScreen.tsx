import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import type { RootStackParamList } from '@app/App';
import { color, size, space } from '@theme/tokens';
import { useResilience } from '@features/resilience/store';

export function HomeScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { continuousDays, resilienceDays, urgesHandledTotal } = useResilience();

  return (
    <View style={styles.container}>
      <View style={styles.streakCard}>
        <Text style={styles.streakLabel}>Resilience</Text>
        <Text style={styles.streakValue}>{resilienceDays} days</Text>
        <Text style={styles.streakSubtle}>
          {urgesHandledTotal} urges handled · never resets
        </Text>
      </View>

      <View style={styles.streakCard}>
        <Text style={styles.streakLabel}>Continuous</Text>
        <Text style={styles.streakValue}>{continuousDays} days</Text>
      </View>

      <Pressable style={styles.primary} onPress={() => navigation.navigate('UrgeLog')}>
        <Text style={styles.primaryText}>Log an urge</Text>
      </Pressable>

      <Pressable style={styles.sos} onPress={() => navigation.navigate('Crisis')}>
        <Text style={styles.sosText}>Need help now</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: color.offWhite,
    padding: space.lg,
    gap: space.md,
  },
  streakCard: {
    backgroundColor: color.mist,
    padding: space.lg,
    borderRadius: 16,
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
  primary: {
    backgroundColor: color.signalBlue,
    padding: space.lg,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: space.lg,
  },
  primaryText: {
    color: color.offWhite,
    fontSize: size.subhead,
  },
  sos: {
    backgroundColor: color.graphite,
    padding: space.lg,
    borderRadius: 16,
    alignItems: 'center',
  },
  sosText: {
    color: color.offWhite,
    fontSize: size.subhead,
  },
});
