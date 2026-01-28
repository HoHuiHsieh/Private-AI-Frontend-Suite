import * as React from 'react';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import ColorModeSelect from '../Settings/ColorModeSelect';
import FontSizeSelect from '../Settings/FontSizeSelect';

const settings = [
    {
        name: 'Color mode',
        desc: 'Select preferred color scheme: light, dark, or system mode',
        item: <ColorModeSelect />,
    },
    {
        name: 'Font size',
        desc: 'Adjust the global font size for better readability',
        item: <FontSizeSelect />,
    },
];

/**
 * Settings component
 * @returns 
 */
export default function Settings() {
    return (
        <React.Fragment>
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    flexGrow: 1,
                    width: '100%',
                    maxWidth: '80%',
                    p: 4,
                }}
            >
                <Typography component="h2" variant="h6" sx={{ mb: 2 }}>
                    Settings
                </Typography>
                <List disablePadding>
                    {settings.map((product) => (
                        <ListItem key={product.name} sx={{ py: 1, px: 0 }}>
                            <ListItemText
                                sx={{ mr: 2 }}
                                primary={product.name}
                                secondary={product.desc}
                            />
                            {product.item}
                        </ListItem>
                    ))}
                </List>
            </Box>
        </React.Fragment>
    );
}