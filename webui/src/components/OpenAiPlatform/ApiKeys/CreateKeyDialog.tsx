import React, { useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Alert from '@mui/material/Alert';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';

interface CreateKeyDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (keyName: string, days: number | null) => void;
    createdKey?: string | null;
}

export default function CreateKeyDialog({ open, onClose, onConfirm, createdKey }: CreateKeyDialogProps) {
    const [keyName, setKeyName] = useState('');
    const [copied, setCopied] = useState(false);
    const [expirationDays, setExpirationDays] = useState<number | string>(365);

    const handleConfirm = () => {
        if (keyName.trim()) {
            const days = expirationDays === '' ? null : Number(expirationDays);
            onConfirm(keyName.trim(), days);
            setKeyName('');
            setExpirationDays(365);
        }
    };

    const handleClose = () => {
        setKeyName('');
        setCopied(false);
        setExpirationDays(365);
        onClose();
    };

    const handleCopy = async () => {
        if (createdKey) {
            await navigator.clipboard.writeText(createdKey);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="sm"
            fullWidth
        >
            <DialogTitle>{createdKey ? 'API Key Created' : 'Create new secret key'}</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 1 }}>
                    {createdKey ? (
                        <>
                            <Alert severity="success" sx={{ mb: 2 }}>
                                Your API key has been created successfully!
                            </Alert>
                            <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                                Please save this secret key somewhere safe and accessible. For security reasons, you won't be able to view it again.
                            </Typography>
                            <TextField
                                fullWidth
                                value={createdKey}
                                variant="outlined"
                                size="small"
                                slotProps={{
                                    input: {
                                        readOnly: true,
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    onClick={handleCopy}
                                                    edge="end"
                                                    color={copied ? 'success' : 'default'}
                                                    sx={{ fontSize: '1rem' }}
                                                >
                                                    <ContentCopyIcon sx={{ fontSize: '1rem' }} />
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                    }
                                }}
                            />
                            {copied && (
                                <Typography variant="caption" color="success.main" sx={{ mt: 1, display: 'block' }}>
                                    Copied to clipboard!
                                </Typography>
                            )}
                        </>
                    ) : (
                        <>
                            <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                                Your secret key will be displayed only once. Make sure to copy and store it securely.
                            </Typography>
                            <TextField
                                autoFocus
                                label="Key name"
                                placeholder="My API Key"
                                fullWidth
                                value={keyName}
                                onChange={(e) => setKeyName(e.target.value)}
                                helperText="A descriptive name for your API key"
                                variant="outlined"
                                size="small"
                                sx={{ mb: 2 }}
                            />
                            <FormControl fullWidth size="small">
                                <InputLabel>Expiration</InputLabel>
                                <Select
                                    value={expirationDays}
                                    label="Expiration"
                                    onChange={(e) => setExpirationDays(e.target.value)}
                                >
                                    <MenuItem value={7}>7 days</MenuItem>
                                    <MenuItem value={30}>30 days</MenuItem>
                                    <MenuItem value={60}>60 days</MenuItem>
                                    <MenuItem value={90}>90 days</MenuItem>
                                    <MenuItem value={180}>180 days</MenuItem>
                                    <MenuItem value={365}>365 days</MenuItem>
                                </Select>
                            </FormControl>
                        </>
                    )}
                </Box>
            </DialogContent>
            <DialogActions sx={{ px: 3, pb: 2 }}>
                {createdKey ? (
                    <Button
                        onClick={handleClose}
                        variant="contained"
                        sx={{ fontSize: '1rem' }}
                    >
                        Done
                    </Button>
                ) : (
                    <>
                        <Button
                            onClick={handleClose}
                            color="inherit"
                            sx={{ fontSize: '1rem' }}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleConfirm}
                            variant="contained"
                            disabled={!keyName.trim()}
                            sx={{ fontSize: '1rem' }}
                        >
                            Create
                        </Button>
                    </>
                )}
            </DialogActions>
        </Dialog>
    );
}
