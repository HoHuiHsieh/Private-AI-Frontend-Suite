import React, { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import OutlinedInput from '@mui/material/OutlinedInput';
import MenuItem from '@mui/material/MenuItem';
import FormHelperText from '@mui/material/FormHelperText';
import { userApi } from '@/services/user';

export interface UserData {
    id: number;
    username: string;
    email: string;
    fullname: string;
    password: string;
    active: boolean;
    scopes: string[];
}

interface UserFormDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (userData: UserData) => void;
    mode: 'create' | 'edit';
    user?: UserData | null;
    success?: boolean;
}

const EMPTY_USER: UserData = {
    id: 0,
    username: '',
    email: '',
    fullname: '',
    password: '',
    active: true,
    scopes: []
};

export default function UserFormDialog({ open, onClose, onConfirm, mode, user, success }: UserFormDialogProps) {
    const [userData, setUserData] = useState<UserData>(EMPTY_USER);
    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [availableScopes, setAvailableScopes] = useState<string[]>([]);
    const [loadingScopes, setLoadingScopes] = useState(false);

    const isEditMode = mode === 'edit';

    // Load user data when dialog opens
    useEffect(() => {
        if (open) {
            if (isEditMode && user) {
                setUserData({
                    ...user,
                    password: '' // Don't pre-fill password for security
                });
            } else {
                setUserData(EMPTY_USER);
            }
            fetchAvailableScopes();
        }
    }, [open, user, isEditMode]);

    // Fetch available scopes from API
    const fetchAvailableScopes = async () => {
        setLoadingScopes(true);
        try {
            const scopes = await userApi.getAvailableScopes();
            setAvailableScopes(scopes);
        } catch (error) {
            console.error('Failed to fetch available scopes:', error);
            // Fallback to default scopes on error
            setAvailableScopes(['admin', 'user', 'guest']);
        } finally {
            setLoadingScopes(false);
        }
    };

    const validateForm = () => {
        const newErrors: { [key: string]: string } = {};

        // Username validation (only for create mode)
        if (!isEditMode && !userData.username.trim()) {
            newErrors.username = 'Username is required';
        }

        // Email validation
        if (!userData.email.trim()) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(userData.email)) {
            newErrors.email = 'Email is invalid';
        }

        // Full name validation
        if (!userData.fullname.trim()) {
            newErrors.fullname = 'Full name is required';
        }

        // Password validation
        if (!isEditMode) {
            // Required for create mode
            if (!userData.password.trim()) {
                newErrors.password = 'Password is required';
            } else if (userData.password.length < 8) {
                newErrors.password = 'Password must be at least 8 characters';
            }
        } else {
            // Optional for edit mode, but if provided, validate it
            if (userData.password && userData.password.length < 8) {
                newErrors.password = 'Password must be at least 8 characters';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleConfirm = () => {
        if (validateForm()) {
            onConfirm(userData);
            resetForm();
        }
    };

    const handleClose = () => {
        resetForm();
        onClose();
    };

    const resetForm = () => {
        setUserData(EMPTY_USER);
        setErrors({});
    };

    const handleChange = (field: keyof UserData) => (event: React.ChangeEvent<HTMLInputElement>) => {
        if (field === 'active') {
            setUserData({ ...userData, [field]: event.target.checked });
        } else {
            setUserData({ ...userData, [field]: event.target.value });
        }
        // Clear error for this field when user starts typing
        if (errors[field]) {
            setErrors({ ...errors, [field]: '' });
        }
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="sm"
            fullWidth
        >
            <DialogTitle>{isEditMode ? 'Edit User' : 'Create New User'}</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 1 }}>
                    {success && (
                        <Alert severity="success" sx={{ mb: 2 }}>
                            User has been {isEditMode ? 'updated' : 'created'} successfully!
                        </Alert>
                    )}
                    <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                        {isEditMode
                            ? 'Update user information. Leave password blank to keep current password.'
                            : 'Fill in the details to create a new user account.'}
                    </Typography>
                    <TextField
                        autoFocus={!isEditMode}
                        margin="dense"
                        label="Username"
                        type="text"
                        fullWidth
                        required={!isEditMode}
                        disabled={isEditMode}
                        value={userData.username}
                        onChange={handleChange('username')}
                        error={!!errors.username}
                        helperText={isEditMode ? 'Username cannot be changed' : errors.username}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        autoFocus={isEditMode}
                        margin="dense"
                        label="Email"
                        type="email"
                        fullWidth
                        required
                        value={userData.email}
                        onChange={handleChange('email')}
                        error={!!errors.email}
                        helperText={errors.email}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        label="Full Name"
                        type="text"
                        fullWidth
                        required
                        value={userData.fullname}
                        onChange={handleChange('fullname')}
                        error={!!errors.fullname}
                        helperText={errors.fullname}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        label={isEditMode ? 'New Password' : 'Password'}
                        type="password"
                        fullWidth
                        required={!isEditMode}
                        value={userData.password}
                        onChange={handleChange('password')}
                        error={!!errors.password}
                        helperText={
                            errors.password ||
                            (isEditMode
                                ? 'Leave blank to keep current password (minimum 8 characters if changing)'
                                : 'Minimum 8 characters')
                        }
                        sx={{ mb: 2 }}
                    />
                    <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel id="multiple-scopes-label">Scopes</InputLabel>
                        <Select<string[]>
                            labelId="multiple-scopes-label"
                            id="multiple-scopes"
                            multiple
                            value={userData.scopes}
                            disabled={loadingScopes}
                            onChange={(event: SelectChangeEvent<string[]>) => {
                                const value = event.target.value;
                                setUserData({ ...userData, scopes: typeof value === 'string' ? value.split(',') : value });
                            }}
                            input={<OutlinedInput id="select-multiple-scopes" label="Scopes" />}
                            renderValue={(selected) => (
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {selected.map((value) => (
                                        <Chip key={value} label={value} size="small" />
                                    ))}
                                </Box>
                            )}
                            MenuProps={{
                                PaperProps: {
                                    style: {
                                        maxHeight: 48 * 4.5 + 8,
                                        width: 250,
                                    },
                                },
                            }}
                            endAdornment={
                                loadingScopes ? (
                                    <CircularProgress
                                        color="inherit"
                                        size={16}
                                        sx={{ position: 'absolute', right: 32, pointerEvents: 'none' }}
                                    />
                                ) : null
                            }
                        >
                            {availableScopes.map((scope) => (
                                <MenuItem key={scope} value={scope}>
                                    {scope}
                                </MenuItem>
                            ))}
                        </Select>
                        <FormHelperText>Select one or more permission scopes for this user</FormHelperText>
                    </FormControl>
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={userData.active}
                                onChange={handleChange('active')}
                            />
                        }
                        label="Active"
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} sx={{ fontSize: '1rem' }}>
                    Cancel
                </Button>
                <Button onClick={handleConfirm} variant="contained" disabled={!!success} sx={{ fontSize: '1rem' }}>
                    {isEditMode ? 'Update User' : 'Create User'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}
