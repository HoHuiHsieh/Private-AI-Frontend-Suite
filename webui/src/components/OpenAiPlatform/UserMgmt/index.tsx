import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import type { GridRowsProp, GridColDef } from '@mui/x-data-grid';
import CustomizedDataGrid from '../CustomizedDataGrid';
import CreateUserDialog, { UserData } from './CreateUserDialog';
import EditUserDialog from './EditUserDialog';
import { userApi, UserCreate, UserUpdate } from '@/services/user';


// Sample data structure for users
// This is just a placeholder. In a real application, you would fetch this data from your backend or database.
const sampleRows: GridRowsProp<UserData> = [
    {
        id: 1,
        username: 'johndoe',
        email: 'johndoe@example.com',
        fullname: 'John Doe',
        password: 'password123',
        active: true,
        scopes: ['user']
    },
    {
        id: 2,
        username: 'janedoe',
        email: 'janedoe@example.com',
        fullname: 'Jane Doe',
        password: 'password456',
        active: true,
        scopes: ['admin']
    },
    {
        id: 3,
        username: 'bobsmith',
        email: 'bobsmith@example.com',
        fullname: 'Bob Smith',
        password: 'password789',
        active: false,
        scopes: ['user']
    }
];
export default function UserMgmt() {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<UserData | null>(null);
    const [success, setSuccess] = useState(false);
    const [editSuccess, setEditSuccess] = useState(false);
    const [rows, setRows] = useState<GridRowsProp<UserData>>([]);
    const [loading, setLoading] = useState(false);

    // Fetch users on component mount
    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const users = await userApi.listUsers();
            // Map API response to UserData format
            const mappedUsers = users.map(user => ({
                ...user,
                password: '' // Don't expose passwords
            }));
            setRows(mappedUsers);
        } catch (error) {
            console.error('Failed to fetch users:', error);
            // Fallback to sample data on error
            setRows(sampleRows);
        } finally {
            setLoading(false);
        }
    };

    // Handle user editing
    const handleEditUser = (user: UserData) => {
        setSelectedUser(user);
        setEditDialogOpen(true);
    };

    // Handle user update
    const handleUpdateUser = async (userData: UserData) => {
        try {
            const userUpdate: UserUpdate = {
                email: userData.email,
                fullname: userData.fullname,
                active: userData.active,
                scopes: userData.scopes
            };
            
            // Include password only if it was changed
            if (userData.password) {
                userUpdate.password = userData.password;
            }
            
            const updatedUser = await userApi.updateUser(userData.username, userUpdate);
            
            // Show success message
            setEditSuccess(true);
            
            // Refresh user list
            await fetchUsers();
            
            // Close dialog after 2 seconds
            setTimeout(() => {
                setEditSuccess(false);
                setEditDialogOpen(false);
                setSelectedUser(null);
            }, 2000);
        } catch (error) {
            console.error('Failed to update user:', error);
            // TODO: Show error message to user
        }
    };

    const handleEditDialogClose = () => {
        setEditDialogOpen(false);
        setEditSuccess(false);
        setSelectedUser(null);
    };

    const dataColumns: GridColDef<UserData>[] = [
        { field: 'username', headerName: 'Username', flex: 1 },
        { field: 'email', headerName: 'Email', flex: 2 },
        { field: 'fullname', headerName: 'Full Name', flex: 1 },
        { field: 'scopes', headerName: 'Scopes', flex: 1 },
        { field: 'active', headerName: 'Active', flex: 1, type: 'boolean' },
        {
            field: 'actions',
            headerName: 'Actions',
            flex: 1,
            sortable: false,
            renderCell: (params) => (
                <IconButton
                    color="primary"
                    size="small"
                    onClick={() => handleEditUser(params.row)}
                    aria-label="edit user"
                >
                    <EditIcon fontSize="small" />
                </IconButton>
            ),
        },
    ];

    // Handle user creation
    const handleCreateUser = async (userData: UserData) => {
        try {
            const userCreate: UserCreate = {
                username: userData.username,
                email: userData.email,
                fullname: userData.fullname,
                password: userData.password,
                active: userData.active,
                scopes: userData.scopes
            };
            
            const newUser = await userApi.createUser(userCreate);
            
            // Show success message
            setSuccess(true);
            
            // Refresh user list
            await fetchUsers();
            
            // Close dialog after 2 seconds
            setTimeout(() => {
                setSuccess(false);
                setDialogOpen(false);
            }, 2000);
        } catch (error) {
            console.error('Failed to create user:', error);
            // TODO: Show error message to user
        }
    };

    const handleDialogClose = () => {
        setDialogOpen(false);
        setSuccess(false);
    };

    return (
        <Box sx={{ width: '100%', maxWidth: { sm: '100%', md: '1700px' }, p: 4 }}>
            <Typography component="h2" variant="h6" sx={{ mb: 2 }}>
                User Management
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    size="small"
                    sx={{ fontSize: '1rem' }}
                    onClick={() => setDialogOpen(true)}
                >
                    Add User
                </Button>
            </Box>
            <CustomizedDataGrid columns={dataColumns} rows={rows} />
            <CreateUserDialog
                open={dialogOpen}
                onClose={handleDialogClose}
                onConfirm={handleCreateUser}
                success={success}
            />
            <EditUserDialog
                open={editDialogOpen}
                onClose={handleEditDialogClose}
                onConfirm={handleUpdateUser}
                user={selectedUser}
                success={editSuccess}
            />
        </Box>
    );
}
