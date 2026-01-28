import React from 'react';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import { Divider, IconButton } from '@mui/material';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import LoginIcon from '@mui/icons-material/Login';
import AppRegistrationIcon from '@mui/icons-material/AppRegistration';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import { alpha } from '@mui/material/styles';
import { useApp } from '@/context/AppProvider';
import { useUser } from '@/context/UserProvider';
import SignIn from '@/components/SignIn';
import SignUp from '@/components/SignUp';
import Settings from './Settings';
import About from './About';
import ChatbotPanel from './ChatbotPanel';
import { chatbotApi } from '@/services/chatbot';

const primaryListItems = [
    { id: 'new_chat', icon: <HomeRoundedIcon />, text: 'New Chat', display: (permission: number) => permission >= 10 ? 'block' : 'none' },
    { id: 'login', icon: <LoginIcon />, text: 'Login', display: (permission: number) => permission == 0 ? 'block' : 'none' },
    { id: 'register', icon: <AppRegistrationIcon />, text: 'Register', display: (permission: number) => permission == 0 ? 'block' : 'none' },
];


const secondaryListItems = [
    { id: 'settings', icon: <SettingsIcon />, text: 'Settings', display: (permission: number) => permission > -1 ? 'block' : 'none' },
    { id: 'about', icon: <InfoRoundedIcon />, text: 'About', display: (permission: number) => permission > -1 ? 'block' : 'none' },
];


interface ChatbotProps {
}

/**
 * Chatbot component
 * @returns Chatbot component
 */
export default function Chatbot(props: ChatbotProps) {
    const { selectedItem } = useApp();

    const ITEM_CONTENTS = [
        { id: 'new_chat', label: 'New Chat', component: <ChatbotPanel /> },
        { id: 'login', label: 'Login', component: <SignIn defaultEntry='portal' /> },
        { id: 'register', label: 'Register', component: <SignUp /> },
        { id: 'settings', label: 'Settings', component: <Settings /> },
        { id: 'about', label: 'About', component: <About /> },
    ];

    // Render ChatbotPanel for any selectedItem starting with 'chat-'
    const renderComponent = () => {
        if (selectedItem?.startsWith('chat-')) {
            return <ChatbotPanel />;
        }
        return ITEM_CONTENTS.find(item => item.id === selectedItem)?.component;
    };

    return (
        <Box
            component="main"
            sx={(theme) => ({
                flexGrow: 1,
                backgroundColor: theme.vars
                    ? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
                    : alpha(theme.palette.background.default, 1),
                overflow: 'hidden',
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
            })}
        >
            {renderComponent()}
        </Box>
    )
}


/**
 * ChatbotMenuContent component
 * @returns ChatbotMenuContent component
 */
export function ChatbotMenuContent() {
    const { selectedItem, setSelectedItem, chatSession, fetchChatSession } = useApp();
    const { user } = useUser();
    const permissionIndex = user?.role === 'admin' ? 20 : user?.role === 'user' ? 10 : user?.role === 'guest' ? 1 : 0;

    // Handle menu item click
    const handleMenuItemClick = React.useCallback((event: React.MouseEvent<HTMLElement>, key: string) => {
        if (['settings', 'about', 'login', 'register'].includes(key)) {
            setSelectedItem(key);
        } else if (key == 'new_chat') {
            setSelectedItem(`chat-${Date.now()}`);
        } else {
            setSelectedItem(`chat-${key}`);
        }
    }, [setSelectedItem]);

    // Handle session removal
    const handleRemoveSession = React.useCallback((event: React.MouseEvent<HTMLElement>, session_id: string) => {
        chatbotApi.deleteHistory(session_id)
            .then(() => fetchChatSession())
            .then(() => handleMenuItemClick(event, 'new_chat'))
            .catch((error) => {
                console.error("Error removing session:", error);
            });
    }, [fetchChatSession]);

    // Format session ID to local time
    const formatSessionIdToLocalTime = (session_id: string | number) => {
        let date: Date | null = null;
        if (typeof session_id === 'number') {
            // Assume timestamp in ms
            date = new Date(session_id);
        } else if (/^\d{10,}$/.test(session_id)) {
            // String of digits, treat as timestamp (ms or s)
            if (session_id.length === 13) {
                date = new Date(Number(session_id));
            } else if (session_id.length === 10) {
                date = new Date(Number(session_id) * 1000);
            } else {
                date = new Date(Number(session_id));
            }
        } else {
            // Try to parse as date string
            date = new Date(session_id);
        }
        if (!date || isNaN(date.getTime())) {
            return String(session_id);
        }
        // Format: YYYY-MM-DD HH:mm:ss
        const pad = (n: number) => n.toString().padStart(2, '0');
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
            `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    }

    return (
        <Stack sx={{ flexGrow: 1, p: 1, justifyContent: 'space-between' }}>

            {/* Primary list items */}
            <List dense>
                <MapListItems
                    data={primaryListItems}
                    permissionIndex={permissionIndex}
                    selected={selectedItem}
                    handleMenuItemClick={handleMenuItemClick}
                />
                <Divider sx={{ my: 1 }} />
                <Box sx={{ p: 0, m: 0, maxHeight: '55vh', overflow: 'auto', width: '100%' }}>
                    {chatSession.map((item) => (
                        <ListItem key={item.session_id}
                            disablePadding
                            sx={{
                                display: permissionIndex >= 10 ? 'flex' : 'none',
                                flexDirection: 'row',
                            }}
                        >
                            <ListItemIcon>
                                <IconButton
                                    size="small"
                                    sx={{ p: 0, mr: 1 }}
                                    onClick={(event) => handleRemoveSession(event, item.session_id)}
                                >
                                    <DeleteForeverIcon fontSize="small" />
                                </IconButton>
                            </ListItemIcon>
                            <ListItemButton
                                selected={selectedItem === `chat-${item.session_id}`}
                                onClick={(event) => handleMenuItemClick(event, item.session_id)}
                                sx={{ display: 'flex', alignItems: 'center' }}
                            >
                                <ListItemText
                                    primary={item.title}
                                    secondary={formatSessionIdToLocalTime(item.session_id)}
                                    sx={{
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        fontSize: '1rem',
                                        m: 0, mb: 1, mt: 1
                                    }}
                                />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </Box>
            </List>

            {/* Secondary List Items */}
            <List dense>
                <Divider sx={{ my: 1 }} />
                <MapListItems
                    data={secondaryListItems}
                    permissionIndex={permissionIndex}
                    selected={selectedItem}
                    handleMenuItemClick={handleMenuItemClick}
                />
            </List>

        </Stack >
    );
}


type MapListItemsProps = {
    data: any[];
    permissionIndex: number;
    selected: string;
    handleMenuItemClick: (event: React.MouseEvent<HTMLElement>, key: string) => void;
}

/**
 * MapListItems component
 * @param props 
 * @returns 
 */
function MapListItems(props: MapListItemsProps) {
    const { data, permissionIndex, selected, handleMenuItemClick } = props;
    return (
        <>
            {data.map((item) => (
                <ListItem key={item.id} disablePadding sx={{ display: item.display(permissionIndex) }}>
                    <ListItemButton
                        selected={selected === item.id}
                        onClick={(event) => handleMenuItemClick(event, item.id)}
                    >
                        <ListItemIcon>{item.icon}</ListItemIcon>
                        <ListItemText primary={item.text} />
                    </ListItemButton>
                </ListItem>
            ))}
        </>
    );
}
