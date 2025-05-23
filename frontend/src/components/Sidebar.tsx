import { Box, IconButton, List, ListItem, ListItemButton, ListItemText, Paper, Typography, Menu, MenuItem } from '@mui/material';
import { Add as AddIcon, MoreVert as MoreVertIcon } from '@mui/icons-material';
import ViewSidebarRoundedIcon from '@mui/icons-material/ViewSidebarRounded';
import { useState } from 'react';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
}

interface Chat {
  _id: string;
  name: string;
  messages: Message[];
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  chatList: Chat[];
  onSelectChat: (chat: Chat) => void;
  onRenameChat: (chatId: string, newName: string) => Promise<void>;
  onDeleteChat: (chatId: string) => Promise<void>;
}

const Sidebar = ({ isOpen, onToggle, onNewChat, chatList, onSelectChat, onRenameChat, onDeleteChat }: SidebarProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newChatName, setNewChatName] = useState('');

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, chatId: string) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedChatId(chatId);
    const chat = chatList.find(c => c._id === chatId);
    if (chat) {
      setNewChatName(chat.name);
    }
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedChatId(null);
    setIsRenaming(false);
  };

  const handleRenameClick = () => {
    setIsRenaming(true);
  };

  const handleRenameSubmit = async () => {
    if (selectedChatId && newChatName.trim()) {
      try {
        await onRenameChat(selectedChatId, newChatName.trim());
        handleMenuClose();
      } catch (error) {
        console.error('Error renaming chat:', error);
      }
    }
  };

  const handleDeleteClick = async () => {
    if (selectedChatId) {
      try {
        await onDeleteChat(selectedChatId);
        handleMenuClose();
      } catch (error) {
        console.error('Error deleting chat:', error);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      handleMenuClose();
    }
  };

  return (
    <Paper
      sx={{
        width: isOpen ? 280 : 80,
        height: '100%',
        transition: 'width 0.3s ease',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#EFEDEC',
        borderRight: '2px solid #E2E0DF',
        boxShadow: 'none'
      }}
      elevation={3}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', pl: "18px", gap: 1 }}>
        <IconButton onClick={onToggle} sx={{
          '&:focus': {
            outline: 'none'
          },
          '&:hover .sidebar-icon': {
            color: '#333',
          }
        }}>
          <ViewSidebarRoundedIcon className="sidebar-icon" sx={{ fontSize: '26px', color: '#545454', }} />
        </IconButton>
        {isOpen && (
          <Typography
            variant="h6"
            sx={{
              fontWeight: 900,
              fontSize: '22px',
              color: '#333',
              letterSpacing: 1,
              ml: 1
            }}
          >
            ProBot
          </Typography>
        )}
      </Box>

      <Box
        onClick={onNewChat}
        sx={isOpen ? { 
          display: 'flex', 
          alignItems: 'center', 
          gap: 2, 
          pl: "22px",
          cursor: 'pointer',
          py: "5px",
          borderRadius: '8px',
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
            '& .add-button': {
              backgroundColor: 'black',
            }
          }
        }: {
          display: 'flex', 
          alignItems: 'center', 
          gap: 2, 
          pl: "22px",
          py: "5px",
          cursor: 'pointer',
          borderRadius: '8px',
        }}
      >
        <IconButton
          className="add-button"
          onClick={onNewChat}
          sx={{
            backgroundColor: '#545454',
            color: 'white',
            '&:hover': {
              backgroundColor: 'black',
            },
            '&:focus': {
              outline: 'none'
            },
            width: '35px',
            height: '35px',
            borderRadius: '8px',
            '& .MuiSvgIcon-root': {
              fontSize: '20px'
            }
          }}
        >
          <AddIcon />
        </IconButton>
        <Typography
          variant="subtitle2"
          onClick={onNewChat}
          sx={{
            color: 'black',
            fontSize: '16px',
            whiteSpace: 'nowrap',
            minWidth: '80px',
            opacity: isOpen ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
        >
          New Chat
        </Typography>
      </Box>

      <Box sx={{ 
        flex: 1, 
        overflow: isOpen ? 'auto' : 'hidden',
        pl: "10px",
        '&::-webkit-scrollbar': {
          width: '6px',
        },
        '&::-webkit-scrollbar-track': {
          background: 'transparent',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#888',
          borderRadius: '3px',
        },
        '&::-webkit-scrollbar-thumb:hover': {
          background: '#555',
        },
      }}>
        <Typography
          variant="subtitle2"
          sx={{
            px: 2,
            mt: "25px",
            mb: "10px",
            color: 'text.secondary',
            whiteSpace: 'nowrap',
            opacity: isOpen ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
        >
          Recent Chats
        </Typography>
        <List sx={{ pt: "0" }}>
          {chatList.map((chat) => (
            <ListItem 
              key={chat._id} 
              disablePadding
              secondaryAction={
                isOpen && (
                  <IconButton
                    edge="end"
                    onClick={(e) => handleMenuClick(e, chat._id)}
                    sx={{
                      opacity: selectedChatId === chat._id ? 1 : 0,
                      transition: 'opacity 0.2s ease',
                      '&:hover': {
                        backgroundColor: 'rgba(0, 0, 0, 0.04)',
                      },
                      '.MuiListItem-root:hover &': {
                        opacity: 1,
                      },
                      '.MuiListItem-root:hover &, &.Mui-focusVisible': {
                        opacity: 1,
                      }
                    }}
                  >
                    <MoreVertIcon />
                  </IconButton>
                )
              }
            >
              <ListItemButton
                onClick={() => onSelectChat(chat)}
                sx={{
                  borderRadius: '8px',
                  mx: 1,
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  }
                }}
              >
                {isRenaming && selectedChatId === chat._id ? (
                  <input
                    type="text"
                    value={newChatName}
                    onChange={(e) => setNewChatName(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onBlur={handleRenameSubmit}
                    autoFocus
                    style={{
                      border: 'none',
                      outline: 'none',
                      background: 'transparent',
                      width: '100%',
                      fontSize: '14px',
                      fontFamily: 'inherit'
                    }}
                  />
                ) : (
                  <ListItemText
                    primary={chat.name}
                    primaryTypographyProps={{
                      sx: {
                        fontSize: '14px',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        opacity: isOpen ? 1 : 0,
                        transition: 'opacity 0.3s ease',
                      }
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            mt: 1,
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            borderRadius: '8px',
          }
        }}
      >
        <MenuItem onClick={handleRenameClick}>Rename</MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>Delete</MenuItem>
      </Menu>
    </Paper>
  );
};

export default Sidebar; 