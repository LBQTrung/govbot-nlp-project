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

  const handleSend = async () => {
    if (message.trim() === '') return;

    const userMsg: Message = {
      sender: 'user',
      text: message.trim(),
    };
    setMessages(prev => [...prev, userMsg]);
    setMessage('');
    setIsLoading(true);
    
    try {
      let currentChatId = chatId;
      
      // If no chat is selected, create a new one
      if (!currentChatId) {
        const createChatResponse = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: userMsg.text.slice(0, 30) + (userMsg.text.length > 30 ? '...' : '')
          })
        });

        const createChatData = await createChatResponse.json();
        if (createChatData.status === 'success') {
          currentChatId = createChatData.data._id;
          setChatId(currentChatId);
        } else {
          throw new Error('Failed to create new chat');
        }
      }

      // Call chat API to send message
      const response = await fetch('http://localhost:8000/api/messages/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          chat_id: currentChatId,
          content: userMsg.text
        })
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        const botMessage: Message = {
          sender: 'bot',
          text: data.data.content
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        throw new Error('Failed to get response from chat API');
      }
    } catch (error) {
      console.error('Error getting response:', error);
      const errorMessage: Message = {
        sender: 'bot',
        text: 'Sorry, I encountered an error. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
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