import './Chat.css';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import ArrowUpwardRoundedIcon from '@mui/icons-material/ArrowUpwardRounded';
import { useEffect, useRef } from 'react';

interface ChatInputProps {
  message: string;
  setMessage: (msg: string) => void;
  handleSend: () => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  setShowProductDetails: (show: boolean) => void;
}

const ChatInput = ({ message, setMessage, handleSend, handleKeyDown, setShowProductDetails }: ChatInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate new height (24px per line)
    const newHeight = Math.min(textarea.scrollHeight, 24 * 7); // 7 lines max
    textarea.style.height = `${newHeight}px`;
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          className="chat-input-text"
          placeholder="Ask anything"
          value={message}
          onChange={e => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          style={{
            minHeight: '24px',
            maxHeight: '168px', // 7 lines * 24px
            overflowY: 'auto',
            color: '#545454',
            resize: 'none',
          }}
        />
        <div className="chat-input-actions">
          <button 
            className="product-details-btn" 
            type="button"
            onClick={() => setShowProductDetails(true)}
          >
            <InfoRoundedIcon /> Product details
          </button>
          <button className="send-btn" type="button" onClick={handleSend}>
            <ArrowUpwardRoundedIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInput; 