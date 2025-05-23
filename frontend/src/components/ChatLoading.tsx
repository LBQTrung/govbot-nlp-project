import React from 'react';
import './Chat.css';

const ChatLoading = () => {
  return (
    <div className="chat-message-row bot">
      <div className="chat-message bot">
        <div className="chat-loading">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
};

export default ChatLoading; 