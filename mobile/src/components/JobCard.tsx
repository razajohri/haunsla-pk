import { formatDistanceToNow } from 'date-fns';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type { Job } from '../types/job';
import { colors, radius, spacing } from '../theme';

type Props = {
  job: Job;
  onPress: () => void;
  onToggleSave?: () => void;
  saved?: boolean;
};

function formatSalary(job: Job): string | null {
  if (!job.salary_min && !job.salary_max) return null;
  const currency = job.salary_currency ?? 'USD';
  if (job.salary_min && job.salary_max) {
    return `${currency} ${job.salary_min.toLocaleString()}–${job.salary_max.toLocaleString()}`;
  }
  const value = job.salary_min ?? job.salary_max;
  return `${currency} ${value?.toLocaleString()}`;
}

export function JobCard({ job, onPress, onToggleSave, saved }: Props) {
  const salary = formatSalary(job);
  const posted = job.posted_at
    ? formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })
    : null;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.topRow}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>
            {job.company.slice(0, 1).toUpperCase()}
          </Text>
        </View>
        <View style={styles.meta}>
          <Text style={styles.company} numberOfLines={1}>
            {job.company}
          </Text>
          {posted ? <Text style={styles.posted}>{posted}</Text> : null}
        </View>
        {job.is_featured ? (
          <View style={styles.featured}>
            <Text style={styles.featuredText}>Featured</Text>
          </View>
        ) : null}
        {onToggleSave ? (
          <Pressable onPress={onToggleSave} hitSlop={12} style={styles.saveBtn}>
            <Text style={styles.saveIcon}>{saved ? '★' : '☆'}</Text>
          </Pressable>
        ) : null}
      </View>

      <Text style={styles.title}>{job.title}</Text>

      {salary ? <Text style={styles.salary}>{salary}</Text> : null}

      <View style={styles.tags}>
        {(job.tags?.length ? job.tags : ['Remote']).slice(0, 4).map((tag) => (
          <View key={tag} style={styles.tag}>
            <Text style={styles.tagText}>{tag}</Text>
          </View>
        ))}
      </View>
    </Pressable>
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
  pressed: {
    opacity: 0.92,
    transform: [{ scale: 0.995 }],
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  logo: {
    width: 40,
    height: 40,
    borderRadius: radius.sm,
    backgroundColor: colors.mint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontFamily: 'DMSans_700Bold',
    color: colors.forestDeep,
    fontSize: 16,
  },
  meta: {
    flex: 1,
  },
  company: {
    fontFamily: 'DMSans_500Medium',
    color: colors.ink,
    fontSize: 14,
  },
  posted: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkFaint,
    fontSize: 12,
    marginTop: 2,
  },
  featured: {
    backgroundColor: colors.saffronSoft,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  featuredText: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
    fontSize: 11,
  },
  saveBtn: {
    padding: 4,
  },
  saveIcon: {
    fontSize: 20,
    color: colors.saffron,
  },
  title: {
    fontFamily: 'Fraunces_600SemiBold',
    fontSize: 22,
    lineHeight: 28,
    color: colors.ink,
    marginBottom: spacing.sm,
  },
  salary: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.forest,
    fontSize: 14,
    marginBottom: spacing.md,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    backgroundColor: colors.mint,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
  },
  tagText: {
    fontFamily: 'DMSans_500Medium',
    color: colors.forestDeep,
    fontSize: 12,
  },
});
