import { Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { FeedScreen } from '../screens/FeedScreen';
import { SearchScreen } from '../screens/SearchScreen';
import { SavedScreen } from '../screens/SavedScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { JobDetailScreen } from '../screens/JobDetailScreen';
import { OnboardingScreen } from '../screens/OnboardingScreen';
import { useAppStore } from '../store/appStore';
import { colors } from '../theme';
import type { MainTabParamList, RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

function TabLabel({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text
      style={{
        fontFamily: focused ? 'DMSans_700Bold' : 'DMSans_500Medium',
        fontSize: 11,
        color: focused ? colors.forest : colors.inkFaint,
      }}
    >
      {label}
    </Text>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.paperElevated,
          borderTopColor: colors.border,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarActiveTintColor: colors.forest,
        tabBarInactiveTintColor: colors.inkFaint,
      }}
    >
      <Tab.Screen
        name="Feed"
        component={FeedScreen}
        options={{
          tabBarLabel: ({ focused }) => <TabLabel label="Feed" focused={focused} />,
          tabBarIcon: () => null,
        }}
      />
      <Tab.Screen
        name="Search"
        component={SearchScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <TabLabel label="Search" focused={focused} />
          ),
          tabBarIcon: () => null,
        }}
      />
      <Tab.Screen
        name="Saved"
        component={SavedScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <TabLabel label="Saved" focused={focused} />
          ),
          tabBarIcon: () => null,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <TabLabel label="Profile" focused={focused} />
          ),
          tabBarIcon: () => null,
        }}
      />
    </Tab.Navigator>
  );
}

export function RootNavigator() {
  const onboardingDone = useAppStore((s) => s.onboardingDone);

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerTintColor: colors.forestDeep,
          headerStyle: { backgroundColor: colors.paper },
          headerTitleStyle: { fontFamily: 'DMSans_600SemiBold' },
          contentStyle: { backgroundColor: colors.paper },
        }}
      >
        {!onboardingDone ? (
          <Stack.Screen
            name="Onboarding"
            component={OnboardingScreen}
            options={{ headerShown: false }}
          />
        ) : (
          <>
            <Stack.Screen
              name="MainTabs"
              component={MainTabs}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="JobDetail"
              component={JobDetailScreen}
              options={{ title: 'Job' }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
