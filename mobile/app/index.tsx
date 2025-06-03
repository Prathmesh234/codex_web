import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { API_URL } from '../constants/Api';

interface Message {
  text: string;
  isUser: boolean;
  timestamp: string;
}

const formatTime = () => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
  }).format(new Date());
};

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (flatListRef.current) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = { text: inputValue, isUser: true, timestamp: formatTime() };
    setMessages(prev => [...prev, userMessage]);

    const question = inputValue;
    setInputValue('');

    try {
      const res = await fetch(`${API_URL}/api/run-browser-task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_question: question, user_name: 'Mobile User' })
      });
      const data = await res.json();
      const reply = data.message || data.live_view_url || 'No response';
      const agentMessage: Message = { text: reply, isUser: false, timestamp: formatTime() };
      setMessages(prev => [...prev, agentMessage]);
    } catch (err) {
      const agentMessage: Message = { text: 'Error contacting server.', isUser: false, timestamp: formatTime() };
      setMessages(prev => [...prev, agentMessage]);
    }
  };

  const renderItem = ({ item }: { item: Message }) => (
    <View style={[styles.messageContainer, item.isUser ? styles.userMessage : styles.agentMessage]}>
      <Text style={styles.messageText}>{item.text}</Text>
      <Text style={styles.timestamp}>{item.isUser ? 'You' : 'Agent'} • {item.timestamp}</Text>
    </View>
  );

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Text style={styles.title}>CodexWeb</Text>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(_, i) => i.toString()}
        renderItem={renderItem}
        contentContainerStyle={styles.messages}
      />
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputValue}
          onChangeText={setInputValue}
          placeholder="Type your message"
          multiline
        />
        <TouchableOpacity style={styles.button} onPress={sendMessage}>
          <Text style={styles.buttonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 12, textAlign: 'center' },
  messages: { flexGrow: 1, justifyContent: 'flex-end' },
  messageContainer: { marginBottom: 12, padding: 12, borderRadius: 8, maxWidth: '80%' },
  userMessage: { backgroundColor: '#DBEAFE', alignSelf: 'flex-end' },
  agentMessage: { backgroundColor: '#F1F5F9', alignSelf: 'flex-start' },
  messageText: { fontSize: 16 },
  timestamp: { fontSize: 12, color: '#6B7280', marginTop: 4 },
  inputContainer: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 8, minHeight: 40 },
  button: { backgroundColor: '#2563EB', paddingVertical: 10, paddingHorizontal: 16, borderRadius: 20 },
  buttonText: { color: '#fff', fontWeight: 'bold' },
});

