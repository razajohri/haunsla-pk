import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAppStore } from '../store/appStore';
import { colors, radius, spacing } from '../theme';
import type { JobFilters } from '../types/job';

const CATEGORIES = ['tech', 'design', 'marketing', 'writing', 'support', 'finance'];

type PathId = 'remote' | 'internship' | 'entry';

const PATHS: {
  id: PathId;
  label: string;
  blurb: string;
  experience?: JobFilters['experience'];
}[] = [
  {
    id: 'remote',
    label: 'Remote jobs',
    blurb: 'Worldwide & Pakistan-friendly remote roles',
  },
  {
    id: 'internship',
    label: 'Internships',
    blurb: 'For grads with an FYP but no work experience yet',
    experience: 'internship',
  },
  {
    id: 'entry',
    label: 'First job',
    blurb: 'Junior, trainee & entry roles in PK or remote',
    experience: 'entry',
  },
];

export function OnboardingScreen() {
  const setOnboardingDone = useAppStore((s) => s.setOnboardingDone);
  const setPreferredCategories = useAppStore((s) => s.setPreferredCategories);
  const setFilters = useAppStore((s) => s.setFilters);
  const [selected, setSelected] = useState<string[]>([]);
  const [path, setPath] = useState<PathId>('remote');

  const toggle = (cat: string) => {
    setSelected((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat],
    );
  };

  const finish = () => {
    setPreferredCategories(selected);
    const chosen = PATHS.find((p) => p.id === path);
    setFilters({
      experience: chosen?.experience,
      category: selected[0],
    });
    setOnboardingDone(true);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.hero}>
        <Text style={styles.brand}>Haunsla</Text>
        <Text style={styles.urdu}>حوصلہ</Text>
        <Text style={styles.tagline}>Remote jobs. Real ambition.</Text>
        <Text style={styles.prompt}>
          We lead with remote roles — and we also help fresh graduates in
          Pakistan find internships and first jobs when all they have is an FYP.
        </Text>
      </View>

      <View>
        <Text style={styles.section}>Where do you want to start?</Text>
        <View style={styles.pathCol}>
          {PATHS.map((p) => {
            const active = path === p.id;
            return (
              <Pressable
                key={p.id}
                onPress={() => setPath(p.id)}
                style={[styles.path, active && styles.pathActive]}
              >
                <Text style={[styles.pathLabel, active && styles.pathLabelActive]}>
                  {p.label}
                </Text>
                <Text style={[styles.pathBlurb, active && styles.pathBlurbActive]}>
                  {p.blurb}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={[styles.section, { marginTop: spacing.lg }]}>
          Categories (optional)
        </Text>
        <View style={styles.grid}>
          {CATEGORIES.map((cat) => {
            const active = selected.includes(cat);
            return (
              <Pressable
                key={cat}
                onPress={() => toggle(cat)}
                style={[styles.chip, active && styles.chipActive]}
              >
                <Text style={[styles.chipText, active && styles.chipTextActive]}>
                  {cat}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Pressable style={styles.cta} onPress={finish}>
        <Text style={styles.ctaText}>Start browsing</Text>
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.paper,
    padding: spacing.lg,
    justifyContent: 'space-between',
  },
  hero: { marginTop: spacing.xl },
  brand: {
    fontFamily: 'Fraunces_700Bold',
    fontSize: 48,
    color: colors.forestDeep,
    letterSpacing: -1,
  },
  urdu: {
    fontFamily: 'Fraunces_600SemiBold',
    fontSize: 24,
    color: colors.forest,
    marginTop: 4,
  },
  tagline: {
    fontFamily: 'DMSans_500Medium',
    fontSize: 18,
    color: colors.ink,
    marginTop: spacing.md,
  },
  prompt: {
    fontFamily: 'DMSans_400Regular',
    fontSize: 15,
    color: colors.inkMuted,
    lineHeight: 22,
    marginTop: spacing.md,
  },
  section: {
    fontFamily: 'DMSans_600SemiBold',
    fontSize: 13,
    color: colors.inkMuted,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  pathCol: { gap: 8 },
  path: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.paperElevated,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pathActive: {
    backgroundColor: colors.forest,
    borderColor: colors.forest,
  },
  pathLabel: {
    fontFamily: 'DMSans_700Bold',
    fontSize: 16,
    color: colors.ink,
  },
  pathLabelActive: { color: colors.white },
  pathBlurb: {
    fontFamily: 'DMSans_400Regular',
    fontSize: 13,
    color: colors.inkMuted,
    marginTop: 4,
    lineHeight: 18,
  },
  pathBlurbActive: { color: 'rgba(255,255,255,0.85)' },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: radius.md,
    backgroundColor: colors.paperElevated,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: {
    backgroundColor: colors.forestDeep,
    borderColor: colors.forestDeep,
  },
  chipText: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
    textTransform: 'capitalize',
  },
  chipTextActive: { color: colors.white },
  cta: {
    backgroundColor: colors.forestDeep,
    paddingVertical: 16,
    borderRadius: radius.md,
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  ctaText: {
    fontFamily: 'DMSans_700Bold',
    color: colors.white,
    fontSize: 16,
  },
});
