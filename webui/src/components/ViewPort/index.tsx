import React from 'react';
import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import SelectContent, { ContentItemProps } from './SelectContent';
import UserCard from './UserCard';

const drawerWidth = 240;

const Drawer = styled(MuiDrawer)({
    width: drawerWidth,
    flexShrink: 0,
    boxSizing: 'border-box',
    mt: 10,
    [`& .${drawerClasses.paper}`]: {
        width: drawerWidth,
        boxSizing: 'border-box',
    },
});

interface ViewPortProps {
    children: React.ReactNode;
    options: ContentItemProps[];
    selectedAPP: string;
    setSelectedAPP: (value: string) => void;
}

/**
 * Side drawer component
 * @returns The side drawer component
 */
export default function ViewPort(props: ViewPortProps) {
    // Skip rendering if no options are available
    if (!props.options || props.options.length === 0) {
        return null;
    }

    return (
        <Drawer
            variant="permanent"
            sx={{
                display: { xs: 'none', md: 'block' },
                [`& .${drawerClasses.paper}`]: {
                    backgroundColor: 'background.paper',
                },
            }}
        >
            <title>{props.selectedAPP.toUpperCase()}</title>
            <Box
                sx={{
                    display: 'flex',
                    mt: 'calc(var(--template-frame-height, 0px) + 4px)',
                    p: 1.5,
                }}
            >
                <SelectContent
                    options={props.options}
                    selectedAPP={props.selectedAPP}
                    setSelectedAPP={props.setSelectedAPP}
                />
            </Box>
            <Divider />
            <Box
                sx={{
                    overflow: 'auto',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                {props.children}
            </Box>
            <UserCard />
        </Drawer>
    );
}
