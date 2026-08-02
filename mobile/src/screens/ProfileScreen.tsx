import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAppStore } from '../store/appStore';
import { colors, spacing } from '../theme';

export function ProfileScreen() {
  const preferredCategories = useAppStore((s) => s.preferredCategories);
  const savedJobIds = useAppStore((s) => s.savedJobIds);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.content}>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.sub}>
          Auth (email + Google) lands in Week 3. For now, preferences stay on-device.
        </Text>

        <View style={styles.block}>
          <Text style={styles.label}>Saved jobs</Text>
          <Text style={styles.value}>{savedJobIds.length}</Text>
        </View>

        <View style={styles.block}>
          <Text style={styles.label}>Preferred categories</Text>
          <Text style={styles.value}>
            {preferredCategories.length
              ? preferredCategories.join(', ')
              : 'Not set'}
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: spacing.lg },
  title: {
    fontFamily: 'Fraunces_700Bold',
    fontSize: 32,
    color: colors.forestDeep,
    marginBottom: spacing.sm,
  },
  sub: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    lineHeight: 22,
    marginBottom: spacing.xl,
  },
  block: {
    marginBottom: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  label: {
    fontFamily: 'DMSans_500Medium',
    color: colors.inkFaint,
    fontSize: 13,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  value: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
    fontSize: 18,
    textTransform: 'capitalize',
  },
});
