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
import { alpha } from '@mui/material/styles';
import { useApp } from '@/context/AppProvider';
import { useUser } from '@/context/UserProvider';
import SignIn from '@/components/SignIn';
import SignUp from '@/components/SignUp';
import Portal from './Portal';
import Settings from './Settings';
import About from './About';


const primaryListItems = [
    { id: 'portal', icon: <HomeRoundedIcon />, text: 'Portal', display: (permission: number) => permission > -1 ? 'block' : 'none' },
    { id: 'login', icon: <LoginIcon />, text: 'Login', display: (permission: number) => permission == 0 ? 'block' : 'none' },
    { id: 'register', icon: <AppRegistrationIcon />, text: 'Register', display: (permission: number) => permission == 0 ? 'block' : 'none' },
];


const secondaryListItems = [
    { id: 'settings', icon: <SettingsIcon />, text: 'Settings', display: (permission: number) => permission > -1 ? 'block' : 'none' },
    { id: 'about', icon: <InfoRoundedIcon />, text: 'About', display: (permission: number) => permission > -1 ? 'block' : 'none' },
];


interface HomePageProps {
    setSelectedAPP: (app: string) => void;
}

/**
 * HomePage component
 * @returns HomePage component
 */
export default function HomePage(props: HomePageProps) {
    const { selectedItem } = useApp();

    const ITEM_CONTENTS = [
        { id: 'portal', label: 'Portal', component: <Portal setSelectedAPP={props.setSelectedAPP} /> },
        { id: 'login', label: 'Login', component: <SignIn defaultEntry='portal' /> },
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
                    justifyContent: "flex-start",
                    alignItems: "stretch",
                    mx: 3,
                    pb: 5,
                    mt: { xs: 8, md: 0 },
                    height: '100%',
                }}
            >
                {ITEM_CONTENTS.find(item => item.id === selectedItem)?.component}
            </Stack>
        </Box>
    )
}


/**
 * HomePageMenuContent component
 * @returns HomePageMenuContent component
 */
export function HomePageMenuContent() {
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
