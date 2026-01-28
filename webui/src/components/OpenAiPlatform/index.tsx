import React from 'react';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import { Divider } from '@mui/material';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import LoginIcon from '@mui/icons-material/Login';
import AppRegistrationIcon from '@mui/icons-material/AppRegistration';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import KeyIcon from '@mui/icons-material/Key';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts';
import { alpha } from '@mui/material/styles';
import { useApp } from '@/context/AppProvider';
import { useUser } from '@/context/UserProvider';
import SignIn from '@/components/SignIn';
import SignUp from '@/components/SignUp';
import Usage from './Usage';
import ApiKeys from './ApiKeys';
import General from './General';
import UserManagement from './UserMgmt';
import Health from './Health';
import Settings from './Settings';
import About from './About';


const primaryListItems = [
    { id: 'general', icon: <HomeRoundedIcon />, text: 'General', display: (permission: number) => permission > -1 ? 'block' : 'none' },
    { id: 'api-keys', icon: <KeyIcon />, text: 'API keys', display: (permission: number) => permission >= 10 ? 'block' : 'none' },
    { id: 'usage', icon: <DataUsageIcon />, text: 'Usage', display: (permission: number) => permission >= 10 ? 'block' : 'none' },
    { id: 'user-management', icon: <ManageAccountsIcon />, text: 'User Management', display: (permission: number) => permission >= 20 ? 'block' : 'none' },
    { id: 'health', icon: <MonitorHeartIcon />, text: 'Service Health', display: (permission: number) => permission >= 20 ? 'block' : 'none' },
    { id: 'login', icon: <LoginIcon />, text: 'Login', display: (permission: number) => permission == 0 ? 'block' : 'none' },
    { id: 'register', icon: <AppRegistrationIcon />, text: 'Register', display: (permission: number) => permission == 0 ? 'block' : 'none' },
];


const secondaryListItems = [
    { id: 'settings', icon: <SettingsIcon />, text: 'Settings', display: (permission: number) => permission > -1 ? 'block' : 'none' },
    { id: 'about', icon: <InfoRoundedIcon />, text: 'About', display: (permission: number) => permission > -1 ? 'block' : 'none' },
];


/**
 * OpenAiPlatform component
 * @returns OpenAiPlatform component
 */
export default function OpenAiPlatform() {
    const { selectedItem } = useApp();

    const ITEM_CONTENTS = [
        { id: 'general', label: 'Portal', component: <General /> },
        { id: 'api-keys', label: 'API Keys', component: <ApiKeys /> },
        { id: 'usage', label: 'Usage', component: <Usage /> },
        { id: 'user-management', label: 'User Management', component: <UserManagement /> },
        { id: 'health', label: 'Service Health', component: <Health /> },
        { id: 'login', label: 'Login', component: <SignIn defaultEntry='general' /> },
        { id: 'register', label: 'Register', component: <SignUp /> },
        { id: 'settings', label: 'Settings', component: <Settings /> },
        { id: 'about', label: 'About', component: <About /> },
    ];

    return (
        <Box
            component="main"
            sx={(theme) => ({
                flexGrow: 1,
                backgroundColor: theme.vars
                    ? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
                    : alpha(theme.palette.background.default, 1),
                overflow: 'auto',
                height: '100vh',
            })}
        >
            <Stack
                spacing={2}
                sx={{
                    alignItems: 'center',
                    mx: 3,
                    pb: 5,
                    mt: { xs: 8, md: 0 },
                }}
            >
                {ITEM_CONTENTS.find(item => item.id === selectedItem)?.component}
            </Stack>
        </Box>
    )
}


/**
 * OpenAiPlatformMenuContent component
 * @returns OpenAiPlatformMenuContent component
 */
export function OpenAiPlatformMenuContent() {
    const { selectedItem, setSelectedItem } = useApp();
    const { user } = useUser();
    const permissionIndex = user?.role === 'admin' ? 20 : user?.role === 'user' ? 10 : user?.role === 'guest' ? 1 : 0;

    // Handle menu item click
    const handleMenuItemClick = React.useCallback((event: React.MouseEvent<HTMLElement>, key: string) => {
        setSelectedItem(key);
    }, [setSelectedItem]);

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

// /**
//  * OpenAiPlatform component
//  * @returns 
//  */
// export default function OpenAiPlatform() {
//     const {  selectedItem, setSelectedItem } = useApp();

//     React.useEffect(() => {
//         if (selectedAPP === 'openai-platform') {
//             setSelectedItem('general');
//         }
//     }, [selectedAPP, setSelectedItem]);

//     if (selectedAPP !== 'openai-platform') {
//         return null;
//     }

//     switch (selectedItem) {
//         case 'general':
//             return (<General />);
//         case 'api-keys':
//             return (<ApiKeys />);
//         case 'usage':
//             return (<Usage />);
//         case 'user-management':
//             return (<UserManagement />);
//         case 'health':
//             return (<Health />);
//         case 'login':
//             return (<SignIn />);
//         case 'register':
//             return (<SignUp />);
//         case 'settings':
//             return (<Settings />);
//         case 'about':
//             return (<About />);
//         default:
//             return null;
//     }
// }