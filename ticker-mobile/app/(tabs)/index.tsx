// app/index.tsx
import React, { useEffect, useState } from 'react';
import { View, FlatList, Linking, StyleSheet, TouchableOpacity } from 'react-native';
import DropDownPicker from 'react-native-dropdown-picker';
import { supabase } from '../../lib/supabase';
import { Colors } from '../../constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { ThemedText } from '@/components/ThemedText';

export default function HomeScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const [dates, setDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [posts, setPosts] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    async function fetchDates() {
      const { data, error } = await supabase
        .from('predictions')
        .select('date')
        .order('date', { ascending: false });

      if (data) {
        const uniqueDates = [...new Set(data.map(p => p.date))];
        setDates(uniqueDates);
        setItems(uniqueDates.map(d => ({ label: d, value: d })));
      }
    }

    fetchDates();
  }, []);

  useEffect(() => {
    async function fetchPosts() {
      if (!selectedDate) return;
      const { data } = await supabase
        .from('predictions')
        .select('*')
        .eq('date', selectedDate)
        .order('created_at', { ascending: false });

      setPosts(data || []);
    }

    fetchPosts();
  }, [selectedDate]);

  const renderPredictionBadge = (label: number) => {
    let text = 'Neutral';
    let color = theme.neutral;
    let icon = '➖';
    if (label === 1) {
      text = 'Up';
      color = theme.up;
      icon = '📈';
    } else if (label === -1) {
      text = 'Down';
      color = theme.down;
      icon = '📉';
    }
    return (
      <View style={[styles.badge, { backgroundColor: color + '22', borderColor: color }]}> 
        <ThemedText style={{ color, fontWeight: 'bold', fontSize: 14 }}>{icon} {text}</ThemedText>
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}> 
      <DropDownPicker
        open={open}
        value={selectedDate}
        items={items}
        setOpen={setOpen}
        setValue={setSelectedDate}
        setItems={setItems}
        placeholder="Select a date"
        style={{ borderColor: theme.tint, marginBottom: 16, backgroundColor: theme.card }}
        dropDownContainerStyle={{ borderColor: theme.tint, backgroundColor: theme.card }}
        textStyle={{ fontFamily: 'SpaceMono', color: theme.text }}
        listItemLabelStyle={{ fontFamily: 'SpaceMono', color: theme.text }}
        selectedItemLabelStyle={{ color: theme.tint }}
      />

      <FlatList
        data={posts}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: 24 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.card, { backgroundColor: theme.card, shadowColor: theme.tint }]}
            activeOpacity={0.85}
            onPress={() => Linking.openURL(item.url)}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
              <ThemedText type="title" style={{ flex: 1 }}>{item.title}</ThemedText>
              {renderPredictionBadge(item.label)}
            </View>
            <ThemedText type="subtitle" style={{ color: theme.tint, marginBottom: 2 }}>
              {item.tickers?.join(', ') || 'No tickers'}
            </ThemedText>
            <ThemedText type="default" style={{ color: theme.icon, fontSize: 13 }}>
              {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
            </ThemedText>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    paddingTop: 32,
    flex: 1,
  },
  card: {
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#E0E3E7',
  },
  badge: {
    borderRadius: 8,
    borderWidth: 1.5,
    paddingHorizontal: 10,
    paddingVertical: 3,
    alignSelf: 'flex-start',
    marginLeft: 8,
  },
});
