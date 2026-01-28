import * as React from 'react';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';


interface ReasoningDialogProps {
    content: string;
    open: boolean;
    onClose: () => void;
}

export default function ReasoningDialog(props: ReasoningDialogProps) {
    const { open, onClose, content } = props;
    const handleClose = () => {
        onClose();
    }
    return (
        <React.Fragment>
            <Dialog
                open={open}
                onClose={handleClose}
                aria-labelledby="reasoning-dialog-title"
                aria-describedby="reasoning-dialog-description"
            >
                <DialogTitle id="reasoning-dialog-title">
                    Reference Details
                </DialogTitle>
                <DialogContent >
                    <DialogContentText id="reasoning-dialog-description" component="div">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                        >
                            {content}
                        </ReactMarkdown>
                    </DialogContentText>
                </DialogContent>
            </Dialog>
        </React.Fragment>
    );
}
