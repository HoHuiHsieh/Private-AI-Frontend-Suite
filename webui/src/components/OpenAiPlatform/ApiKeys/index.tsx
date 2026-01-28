import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import type { GridRowsProp, GridColDef } from '@mui/x-data-grid';
import CustomizedDataGrid from '../CustomizedDataGrid';
import CreateKeyDialog from './CreateKeyDialog';
import { useUser } from '@/context/UserProvider';
import IconButton from '@mui/material/IconButton';
import BlockIcon from '@mui/icons-material/Block';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import { apiKeyService } from '@/services/apikey';


export interface ApiKeyData {
    id: number;
    api_key: string;
    user_id: number;
    expires_at: string;
    revoked: boolean;
}

const sampleRows: GridRowsProp<ApiKeyData> = [
    {
        id: 1,
        api_key: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        user_id: 1,
        expires_at: '2024-12-31T23:59:59Z',
        revoked: false,
    },
    {
        id: 2,
        api_key: 'sk-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy',
        user_id: 1,
        expires_at: '',
        revoked: true,
    },
];


/**
 * ApiKey component
 * @returns 
 */
export default function ApiKeys() {
    const { user } = useUser();
    const [dialogOpen, setDialogOpen] = useState(false);
    const [createdKey, setCreatedKey] = useState<string | null>(null);
    const [rows, setRows] = useState<GridRowsProp<ApiKeyData>>(sampleRows);
    const [loading, setLoading] = useState(false);
    const [showRevoked, setShowRevoked] = useState(false);

    // Fetch API keys on component mount
    useEffect(() => {
        fetchApiKeys();
    }, []);

    // Fetch all API keys for the current user
    const fetchApiKeys = async () => {
        try {
            setLoading(true);
            const keys = await apiKeyService.listKeys();
            setRows(keys);
        } catch (error) {
            console.error('Failed to fetch API keys:', error);
            // Keep showing sample data on error
        } finally {
            setLoading(false);
        }
    };

    // Handle revoking an API key
    const handleRevokeKey = async (keyId: number) => {
        try {
            await apiKeyService.revokeKey(keyId);
            // Update the row to mark as revoked
            setRows(rows.map(row => 
                row.id === keyId ? { ...row, revoked: true } : row
            ));
        } catch (error) {
            console.error('Failed to revoke API key:', error);
        }
    };

    // Handle creating a new API key
    const handleCreateKey = async (keyName: string, days: number | null) => {
        try {
            // Create the new API key with expiration
            const params: { name: string; days?: number } = { name: keyName };
            if (days !== null) {
                params.days = days;
            }
            const newKey = await apiKeyService.createKey(params);
            setCreatedKey(newKey.api_key);
            // Refresh the list to show the new key
            await fetchApiKeys();
        } catch (error) {
            console.error('Failed to create API key:', error);
        }
    };

    // Handle dialog close
    const handleDialogClose = () => {
        setDialogOpen(false);
        setCreatedKey(null);
    };

    const dataColumns: GridColDef<ApiKeyData>[] = [
        {
            field: 'api_key',
            headerName: 'Secret Key',
            flex: 1,
            minWidth: 200,
        },
        {
            field: 'expires_at',
            headerName: 'Expires',
            flex: 1,
            minWidth: 150,
            valueFormatter: (value: string) => {
                return value ? new Date(value).toLocaleDateString() : 'Never';
            },
        },
        {
            field: 'revoked',
            headerName: 'Status',
            flex: 0.5,
            minWidth: 100,
            valueFormatter: (value: boolean) => {
                return value ? 'Revoked' : 'Active';
            },
        },
        {
            field: 'actions',
            headerName: 'Actions',
            flex: 0.5,
            minWidth: 100,
            sortable: false,
            renderCell: (params) => {
                if (params.row.revoked) {
                    return null;
                }
                return (
                    <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleRevokeKey(params.row.id)}
                        title="Revoke key"
                    >
                        <BlockIcon />
                    </IconButton>
                );
            },
        },
    ];

    return (
        <Box sx={{ width: '100%', maxWidth: { sm: '100%', md: '1700px' }, p: 4 }}>
            <Typography component="h2" variant="h6" sx={{ mb: 2 }}>
                API keys
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
                You have permission to view and manage your API keys.
                <br />
                Do not share your API key with others or expose it in the browser or other client-side code.
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={showRevoked}
                            onChange={(e) => setShowRevoked(e.target.checked)}
                            size="small"
                        />
                    }
                    label="Show revoked keys"
                />
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    size="small"
                    sx={{ fontSize: '1rem' }}
                    onClick={() => setDialogOpen(true)}
                >
                    Create new secret key
                </Button>
            </Box>
            <CustomizedDataGrid columns={dataColumns} rows={showRevoked ? rows : rows.filter(row => !row.revoked)} />
            <CreateKeyDialog
                open={dialogOpen}
                onClose={handleDialogClose}
                onConfirm={handleCreateKey}
                createdKey={createdKey}
            />
        </Box>
    );
}
