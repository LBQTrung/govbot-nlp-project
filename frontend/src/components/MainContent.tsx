import { useState, useRef, useEffect } from 'react';
import ChatHistory from './ChatHistory';
import type { Message } from './ChatHistory';
import ChatInput from './ChatInput';
import './Chat.css';

interface Chat {
  _id: string;
  name: string;
  messages: Message[];
}

interface MainContentProps {
  selectedChat: Chat | null;
  onResendMessage?: (messageId: string, chatId: string, content: string) => Promise<void>;
}

const MainContent = ({ selectedChat, onResendMessage }: MainContentProps) => {
  const [chatId, setChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [, setShowProductDetails] = useState(false);

  // Effect to handle selected chat
  useEffect(() => {
    if (selectedChat) {
      setChatId(selectedChat._id);
      setMessages(selectedChat.messages || []);
    } else {
      setChatId(null);
      setMessages([]);
    }
  }, [selectedChat]);

  // Effect to scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = async () => {
    if (message.trim() !== '' && chatId) {
      const userMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'user',
        text: message.trim(),
      };
      setMessages(prev => [...prev, userMsg]);
      setMessage('');
      setIsLoading(true);
      
      try {
        // Call chat API to send message
        const response = await fetch('http://localhost:8000/api/messages/send', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            chat_id: chatId,
            content: userMsg.text
          })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
          const botMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: data.data.content,
            sender: 'bot'
          };
          setMessages(prev => [...prev, botMessage]);
        } else {
          throw new Error('Failed to get response from chat API');
        }
      } catch (error) {
        console.error('Error getting response:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: 'Sorry, I encountered an error. Please try again.',
          sender: 'bot'
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`main-content${messages.length > 0 ? ' no-header' : ''}`}>
      <nav className="navbar">
        <div className="chat-avatar">T</div>
      </nav>
      <div className={`chat-container${messages.length > 0 ? ' no-header' : ''}`}>
        {messages.length > 0 && (
          <ChatHistory 
            messages={messages}
            isLoading={isLoading}
            onResendMessage={onResendMessage}
            chatId={chatId}
          />
        )}
        <div ref={messagesEndRef} />
        {messages.length === 0 && (
          <div className="chat-header">
            <div className="chat-header-title">Chào, Trung.</div>
            <div className="chat-header-desc">Bạn muốn biết gì về thủ tục hành chính công?</div>
          </div>
        )}
        <ChatInput
          message={message}
          setMessage={setMessage}
          handleSend={handleSend}
          handleKeyDown={handleKeyDown}
          setShowProductDetails={setShowProductDetails}
        />
      </div>
    </div>
  );
};

export default MainContent; 