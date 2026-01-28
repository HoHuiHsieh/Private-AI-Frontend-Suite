import React from 'react';
import UserFormDialog, { UserData } from './UserFormDialog';

interface EditUserDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (userData: UserData) => void;
    user: UserData | null;
    success?: boolean;
}

/**
 * EditUserDialog component
 * @param param0 
 * @returns 
 */
export default function EditUserDialog({ open, onClose, onConfirm, user, success }: EditUserDialogProps) {
    return (
        <UserFormDialog
            open={open}
            onClose={onClose}
            onConfirm={onConfirm}
            mode="edit"
            user={user}
            {...(success !== undefined && { success })}
        />
    );
}
