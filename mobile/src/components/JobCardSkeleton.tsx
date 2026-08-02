import { StyleSheet, View } from 'react-native';
import { colors, radius, spacing } from '../theme';

export function JobCardSkeleton() {
  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.avatar} />
        <View style={styles.lines}>
          <View style={[styles.line, { width: '40%' }]} />
          <View style={[styles.line, { width: '25%', marginTop: 6 }]} />
        </View>
      </View>
      <View style={[styles.line, { width: '85%', height: 18, marginTop: 16 }]} />
      <View style={[styles.line, { width: '55%', height: 18, marginTop: 8 }]} />
      <View style={styles.tags}>
        <View style={styles.tag} />
        <View style={styles.tag} />
        <View style={styles.tag} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.paperElevated,
    borderRadius: radius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: radius.sm,
    backgroundColor: colors.border,
  },
  lines: {
    flex: 1,
  },
  line: {
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.border,
  },
  tags: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 16,
  },
  tag: {
    width: 64,
    height: 24,
    borderRadius: 999,
    backgroundColor: colors.border,
  },
});
