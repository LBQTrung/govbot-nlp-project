import './Chat.css';
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded';
import ContentCopyRoundedIcon from '@mui/icons-material/ContentCopyRounded';
import CheckRoundedIcon from '@mui/icons-material/CheckRounded';
import ChatLoading from './ChatLoading';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useState, useCallback } from 'react';

export type Message = {
  sender: 'user' | 'bot';
  text: string;
  chat_id?: string;
};

interface ChatHistoryProps {
  messages: Message[];
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  isLoading: boolean;
  onResendMessage?: (messageIndex: number, chatId: string, content: string) => Promise<void>;
}

const ChatHistory = ({ messages, messagesEndRef, isLoading, onResendMessage }: ChatHistoryProps) => {
  const [copiedMessageIndex, setCopiedMessageIndex] = useState<number | null>(null);
  const [refreshingMessageIndex, setRefreshingMessageIndex] = useState<number | null>(null);

  const handleCopy = useCallback((messageIndex: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageIndex(messageIndex);
    
    // Reset copied state after 2 seconds
    setTimeout(() => {
      setCopiedMessageIndex(null);
    }, 2000);
  }, []);

  const handleResend = async (messageIndex: number, chatId: string, content: string) => {
    if (!onResendMessage) return;
    
    try {
      setRefreshingMessageIndex(messageIndex);
      await onResendMessage(messageIndex, chatId, content);
    } catch (error) {
      console.error('Failed to resend message:', error);
    } finally {
      setRefreshingMessageIndex(null);
    }
  };

  const renderMessageContent = (message: Message, index: number) => {
    if (message.sender === 'bot') {
      return (
        <>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              code: ({ inline, className, children, ...props }: any) => {
                return !inline ? (
                  <div className="code-block">
                    <code className={className} {...props}>
                      {String(children).replace(/\n$/, '')}
                    </code>
                  </div>
                ) : (
                  <code className="inline-code" {...props}>
                    {children}
                  </code>
                );
              },
              a: ({ children, ...props }: any) => (
                <a className="markdown-link" {...props}>
                  {children}
                </a>
              ),
              ul: ({ children, ...props }: any) => (
                <ul className="markdown-list" {...props}>
                  {children}
                </ul>
              ),
              ol: ({ children, ...props }: any) => (
                <ol className="markdown-list" {...props}>
                  {children}
                </ol>
              ),
              h1: ({ children, ...props }: any) => (
                <h1 className="markdown-heading" {...props}>
                  {children}
                </h1>
              ),
              h2: ({ children, ...props }: any) => (
                <h2 className="markdown-heading" {...props}>
                  {children}
                </h2>
              ),
              h3: ({ children, ...props }: any) => (
                <h3 className="markdown-heading" {...props}>
                  {children}
                </h3>
              ),
              blockquote: ({ children, ...props }: any) => (
                <blockquote className="markdown-blockquote" {...props}>
                  {children}
                </blockquote>
              ),
              table: ({ children, ...props }: any) => (
                <div className="markdown-table-container">
                  <table className="markdown-table" {...props}>
                    {children}
                  </table>
                </div>
              ),
            }}
          >
            {message.text}
          </ReactMarkdown>
          <div className="chat-message-actions">
            <button 
              className={`chat-icon-btn ${copiedMessageIndex === index ? 'copied' : ''}`}
              title={copiedMessageIndex === index ? "Copied!" : "Copy"}
              onClick={() => handleCopy(index, message.text)}
            >
              {copiedMessageIndex === index ? <CheckRoundedIcon /> : <ContentCopyRoundedIcon />}
            </button>
            <button 
              className={`chat-icon-btn ${refreshingMessageIndex === index ? 'refreshing' : ''}`}
              title="Resend message"
              onClick={() => {
                if (index > 0 && messages[index - 1].sender === 'user' && message.chat_id) {
                  handleResend(index, message.chat_id, messages[index - 1].text);
                }
              }}
              disabled={refreshingMessageIndex === index}
            >
              <RefreshRoundedIcon className={refreshingMessageIndex === index ? 'rotating' : ''} />
            </button>
          </div>
        </>
      );
    }
    return message.text;
  };

  return (
    <div className="chat-history">
      {messages.map((message, index) => (
        <div key={index} className={`chat-message-row ${message.sender}`}>
          <div className={`chat-message ${message.sender}`}>
            {renderMessageContent(message, index)}
          </div>
        </div>
      ))}
      {isLoading && <ChatLoading />}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatHistory; 