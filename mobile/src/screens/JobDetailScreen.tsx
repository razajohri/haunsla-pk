import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';
import { colors, radius, spacing } from '../theme';
import type { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'JobDetail'>;

export function JobDetailScreen({ route }: Props) {
  const { jobId } = route.params;
  const savedJobIds = useAppStore((s) => s.savedJobIds);
  const toggleSaved = useAppStore((s) => s.toggleSaved);
  const saved = savedJobIds.includes(jobId);

  const query = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId),
  });

  const job = query.data;

  if (query.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.forest} size="large" />
      </View>
    );
  }

  if (!job) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>Job not found</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.company}>{job.company}</Text>
        <Text style={styles.title}>{job.title}</Text>

        <View style={styles.tags}>
          {(job.tags ?? ['Remote']).map((tag) => (
            <View key={tag} style={styles.tag}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>

        {job.salary_min || job.salary_max ? (
          <Text style={styles.salary}>
            {job.salary_currency ?? 'USD'}{' '}
            {job.salary_min?.toLocaleString()}
            {job.salary_max ? `–${job.salary_max.toLocaleString()}` : '+'}
          </Text>
        ) : null}

        <Text style={styles.section}>About the role</Text>
        <Text style={styles.body}>
          {(job.description || 'No description provided.')
            .replace(/<[^>]+>/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()}
        </Text>
      </ScrollView>

      <View style={styles.actions}>
        <Pressable
          style={styles.secondary}
          onPress={() => toggleSaved(job.id)}
        >
          <Text style={styles.secondaryText}>{saved ? 'Saved ★' : 'Save ☆'}</Text>
        </Pressable>
        <Pressable
          style={styles.ghost}
          onPress={() =>
            Share.share({
              message: `${job.title} at ${job.company}\n${job.apply_url}`,
            })
          }
        >
          <Text style={styles.ghostText}>Share</Text>
        </Pressable>
        <Pressable
          style={styles.primary}
          onPress={() => Linking.openURL(job.apply_url)}
        >
          <Text style={styles.primaryText}>Apply</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: spacing.lg, paddingBottom: 120 },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.paper,
  },
  error: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.danger,
  },
  company: {
    fontFamily: 'DMSans_500Medium',
    color: colors.forest,
    fontSize: 14,
    marginBottom: 8,
  },
  title: {
    fontFamily: 'Fraunces_700Bold',
    fontSize: 28,
    lineHeight: 34,
    color: colors.ink,
    marginBottom: spacing.md,
  },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: spacing.md },
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
  salary: {
    fontFamily: 'DMSans_700Bold',
    color: colors.forest,
    fontSize: 16,
    marginBottom: spacing.lg,
  },
  section: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.inkMuted,
    fontSize: 13,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  body: {
    fontFamily: 'DMSans_400Regular',
    color: colors.ink,
    fontSize: 16,
    lineHeight: 26,
  },
  actions: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: 'row',
    gap: 8,
    padding: spacing.md,
    backgroundColor: colors.paperElevated,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  primary: {
    flex: 1.4,
    backgroundColor: colors.forest,
    paddingVertical: 14,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  primaryText: {
    fontFamily: 'DMSans_700Bold',
    color: colors.white,
  },
  secondary: {
    flex: 1,
    backgroundColor: colors.mint,
    paddingVertical: 14,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  secondaryText: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.forestDeep,
  },
  ghost: {
    paddingHorizontal: 12,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ghostText: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.inkMuted,
  },
});
