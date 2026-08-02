import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAppStore } from '../store/appStore';
import { colors, radius, spacing } from '../theme';

const CATEGORIES = ['tech', 'design', 'marketing', 'writing', 'support', 'finance'];

export function OnboardingScreen() {
  const setOnboardingDone = useAppStore((s) => s.setOnboardingDone);
  const setPreferredCategories = useAppStore((s) => s.setPreferredCategories);
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (cat: string) => {
    setSelected((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat],
    );
  };

  const finish = () => {
    setPreferredCategories(selected);
    setOnboardingDone(true);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.hero}>
        <Text style={styles.brand}>Haunsla</Text>
        <Text style={styles.urdu}>حوصلہ</Text>
        <Text style={styles.tagline}>Remote jobs. Real ambition.</Text>
        <Text style={styles.prompt}>
          What are you looking for? Pick a few categories to personalize your feed.
        </Text>
      </View>

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

      <Pressable style={styles.cta} onPress={finish}>
        <Text style={styles.ctaText}>
          {selected.length ? 'Start browsing' : 'Skip for now'}
        </Text>
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
  hero: { marginTop: spacing.xxl },
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
    marginTop: spacing.lg,
  },
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
    backgroundColor: colors.forest,
    borderColor: colors.forest,
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
