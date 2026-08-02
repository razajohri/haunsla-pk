import { useCallback } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../api/client';
import { JobCard } from '../components/JobCard';
import { JobCardSkeleton } from '../components/JobCardSkeleton';
import { useAppStore } from '../store/appStore';
import { colors, spacing } from '../theme';
import type { Job } from '../types/job';
import type { RootStackParamList } from '../navigation/types';

type Nav = NativeStackNavigationProp<RootStackParamList>;

export function FeedScreen() {
  const navigation = useNavigation<Nav>();
  const filters = useAppStore((s) => s.filters);
  const savedJobIds = useAppStore((s) => s.savedJobIds);
  const toggleSaved = useAppStore((s) => s.toggleSaved);

  const query = useInfiniteQuery({
    queryKey: ['jobs', filters],
    queryFn: ({ pageParam = 1 }) => api.getJobs(pageParam, filters),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
  });

  const jobs = query.data?.pages.flatMap((p) => p.items) ?? [];

  const onEndReached = useCallback(() => {
    if (query.hasNextPage && !query.isFetchingNextPage) {
      query.fetchNextPage();
    }
  }, [query]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.brand}>Haunsla</Text>
        <Text style={styles.urdu}>حوصلہ</Text>
        <Text style={styles.sub}>Remote jobs. Real ambition.</Text>
      </View>

      {query.isLoading ? (
        <View style={styles.listPad}>
          <JobCardSkeleton />
          <JobCardSkeleton />
          <JobCardSkeleton />
        </View>
      ) : query.isError ? (
        <View style={styles.center}>
          <Text style={styles.errorTitle}>Couldn’t load jobs</Text>
          <Text style={styles.errorBody}>
            Start the Flask API, then pull to refresh.
          </Text>
        </View>
      ) : (
        <FlashList
          data={jobs}
          keyExtractor={(item: Job) => String(item.id)}
          estimatedItemSize={180}
          contentContainerStyle={styles.listPad}
          onEndReached={onEndReached}
          onEndReachedThreshold={0.4}
          refreshControl={
            <RefreshControl
              refreshing={query.isRefetching && !query.isFetchingNextPage}
              onRefresh={() => query.refetch()}
              tintColor={colors.forest}
            />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.errorTitle}>No jobs yet</Text>
              <Text style={styles.errorBody}>
                Pull to refresh, or run the scrapers on the backend.
              </Text>
            </View>
          }
          ListFooterComponent={
            query.isFetchingNextPage ? (
              <ActivityIndicator color={colors.forest} style={{ marginVertical: 16 }} />
            ) : null
          }
          renderItem={({ item }) => (
            <JobCard
              job={item}
              saved={savedJobIds.includes(item.id)}
              onToggleSave={() => toggleSaved(item.id)}
              onPress={() => navigation.navigate('JobDetail', { jobId: item.id })}
            />
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.paper,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  brand: {
    fontFamily: 'Fraunces_700Bold',
    fontSize: 34,
    color: colors.forestDeep,
    letterSpacing: -0.5,
  },
  urdu: {
    fontFamily: 'Fraunces_600SemiBold',
    fontSize: 18,
    color: colors.forest,
    marginTop: 2,
  },
  sub: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    marginTop: 4,
    fontSize: 14,
  },
  listPad: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  center: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  errorTitle: {
    fontFamily: 'Fraunces_600SemiBold',
    fontSize: 20,
    color: colors.ink,
    marginBottom: 8,
  },
  errorBody: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
});
