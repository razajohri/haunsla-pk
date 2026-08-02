import { useMemo } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../api/client';
import { JobCard } from '../components/JobCard';
import { useAppStore } from '../store/appStore';
import { colors, spacing } from '../theme';
import type { RootStackParamList } from '../navigation/types';

type Nav = NativeStackNavigationProp<RootStackParamList>;

export function SavedScreen() {
  const navigation = useNavigation<Nav>();
  const savedJobIds = useAppStore((s) => s.savedJobIds);
  const toggleSaved = useAppStore((s) => s.toggleSaved);

  const query = useQuery({
    queryKey: ['jobs', 'all-for-saved'],
    queryFn: () => api.getJobs(1, {}),
  });

  const savedJobs = useMemo(() => {
    const items = query.data?.items ?? [];
    return items.filter((j) => savedJobIds.includes(j.id));
  }, [query.data, savedJobIds]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Text style={styles.title}>Saved</Text>
      <FlatList
        data={savedJobs}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>No saved jobs</Text>
            <Text style={styles.emptyBody}>
              Tap the star on a job card to save it for later.
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <JobCard
            job={item}
            saved
            onToggleSave={() => toggleSaved(item.id)}
            onPress={() => navigation.navigate('JobDetail', { jobId: item.id })}
          />
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  title: {
    fontFamily: 'Fraunces_700Bold',
    fontSize: 32,
    color: colors.forestDeep,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    marginBottom: spacing.md,
  },
  list: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxl },
  empty: { padding: spacing.xl, alignItems: 'center' },
  emptyTitle: {
    fontFamily: 'Fraunces_600SemiBold',
    fontSize: 20,
    color: colors.ink,
    marginBottom: 8,
  },
  emptyBody: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    textAlign: 'center',
  },
});
