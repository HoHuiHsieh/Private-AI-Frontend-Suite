import React from 'react';
import UserFormDialog, { UserData } from './UserFormDialog';

export type { UserData };

interface CreateUserDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (userData: UserData) => void;
    success?: boolean;
}

/**
 * CreateUserDialog component
 * @param param0 
 * @returns 
 */
export default function CreateUserDialog({ open, onClose, onConfirm, success }: CreateUserDialogProps) {
    return (
        <UserFormDialog
            open={open}
            onClose={onClose}
            onConfirm={onConfirm}
            mode="create"
            {...(success !== undefined && { success })}
        />
    );
}
