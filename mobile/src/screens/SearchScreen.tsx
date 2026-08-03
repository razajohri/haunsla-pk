import { useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAppStore } from '../store/appStore';
import { colors, radius, spacing } from '../theme';

const CATEGORIES = ['tech', 'design', 'marketing', 'writing', 'support', 'finance'];
const EXPERIENCE: { value: string; label: string }[] = [
  { value: 'internship', label: 'Internships' },
  { value: 'entry', label: 'First job' },
  { value: 'mid', label: 'Mid' },
  { value: 'senior', label: 'Senior' },
];
const JOB_TYPES = ['full-time', 'part-time', 'contract', 'freelance'];
const DATES = [
  { label: 'Today', value: 'today' },
  { label: 'This week', value: 'week' },
  { label: 'This month', value: 'month' },
];

export function SearchScreen() {
  const navigation = useNavigation();
  const filters = useAppStore((s) => s.filters);
  const setFilters = useAppStore((s) => s.setFilters);
  const clearFilters = useAppStore((s) => s.clearFilters);
  const [q, setQ] = useState(filters.q ?? '');

  const apply = () => {
    setFilters({ ...filters, q: q.trim() || undefined });
    navigation.navigate('Feed' as never);
  };

  const Chip = ({
    label,
    active,
    onPress,
  }: {
    label: string;
    active: boolean;
    onPress: () => void;
  }) => (
    <Pressable
      onPress={onPress}
      style={[styles.chip, active && styles.chipActive]}
    >
      <Text style={[styles.chipText, active && styles.chipTextActive]}>
        {label}
      </Text>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Search</Text>
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder="Role, company, keyword…"
          placeholderTextColor={colors.inkFaint}
          style={styles.input}
          returnKeyType="search"
          onSubmitEditing={apply}
        />

        <Text style={styles.section}>Category</Text>
        <View style={styles.row}>
          {CATEGORIES.map((c) => (
            <Chip
              key={c}
              label={c}
              active={filters.category === c}
              onPress={() =>
                setFilters({
                  ...filters,
                  category: filters.category === c ? undefined : c,
                })
              }
            />
          ))}
        </View>

        <Text style={styles.section}>Experience</Text>
        <Text style={styles.hint}>
          Fresh grads: start with Internships or First job — FYP counts as a start.
        </Text>
        <View style={styles.row}>
          {EXPERIENCE.map((e) => (
            <Chip
              key={e.value}
              label={e.label}
              active={filters.experience === e.value}
              onPress={() =>
                setFilters({
                  ...filters,
                  experience:
                    filters.experience === e.value ? undefined : e.value,
                })
              }
            />
          ))}
        </View>

        <Text style={styles.section}>Job type</Text>
        <View style={styles.row}>
          {JOB_TYPES.map((t) => (
            <Chip
              key={t}
              label={t}
              active={filters.job_type === t}
              onPress={() =>
                setFilters({
                  ...filters,
                  job_type: filters.job_type === t ? undefined : t,
                })
              }
            />
          ))}
        </View>

        <Text style={styles.section}>Date posted</Text>
        <View style={styles.row}>
          {DATES.map((d) => (
            <Chip
              key={d.value}
              label={d.label}
              active={filters.date_posted === d.value}
              onPress={() =>
                setFilters({
                  ...filters,
                  date_posted:
                    filters.date_posted === d.value ? undefined : d.value,
                })
              }
            />
          ))}
        </View>

        <Pressable style={styles.primary} onPress={apply}>
          <Text style={styles.primaryText}>Show results</Text>
        </Pressable>
        <Pressable style={styles.secondary} onPress={clearFilters}>
          <Text style={styles.secondaryText}>Clear filters</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: spacing.lg, paddingBottom: spacing.xxl },
  title: {
    fontFamily: 'Fraunces_700Bold',
    fontSize: 32,
    color: colors.forestDeep,
    marginBottom: spacing.lg,
  },
  input: {
    backgroundColor: colors.paperElevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
    fontFamily: 'DMSans_400Regular',
    fontSize: 16,
    color: colors.ink,
    marginBottom: spacing.lg,
  },
  section: {
    fontFamily: 'DMSans_600SemiBold',
    fontSize: 14,
    color: colors.inkMuted,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: colors.paperElevated,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: {
    backgroundColor: colors.forest,
    borderColor: colors.forest,
  },
  chipText: {
    fontFamily: 'DMSans_500Medium',
    color: colors.ink,
    fontSize: 13,
    textTransform: 'capitalize',
  },
  chipTextActive: { color: colors.white },
  primary: {
    marginTop: spacing.xl,
    backgroundColor: colors.forest,
    paddingVertical: 16,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  primaryText: {
    fontFamily: 'DMSans_700Bold',
    color: colors.white,
    fontSize: 16,
  },
  secondary: {
    marginTop: spacing.sm,
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryText: {
    fontFamily: 'DMSans_500Medium',
    color: colors.inkMuted,
  },
});
