

import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


export default function About() {
    const [markdown, setMarkdown] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetch('/static/About.md')
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Failed to load markdown file');
                }
                return response.text();
            })
            .then((text) => {
                setMarkdown(text);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 4 }}>
                <Typography color="error">Error: {error}</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ width: '100%', maxWidth: { sm: '100%', md: '1200px' }, p: 4 }}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h1: ({ node, children, ...props }) => <Typography variant="h4" component="h1" sx={{ mb: 2, mt: 3 }}>{children}</Typography>,
                    h2: ({ node, children, ...props }) => <Typography variant="h5" component="h2" sx={{ mb: 2, mt: 3 }}>{children}</Typography>,
                    h3: ({ node, children, ...props }) => <Typography variant="h6" component="h3" sx={{ mb: 1.5, mt: 2 }}>{children}</Typography>,
                    p: ({ node, children, ...props }) => <Typography variant="body1" component="p" sx={{ mb: 2 }}>{children}</Typography>,
                    li: ({ node, children, ...props }) => <Typography variant="body1" component="li" sx={{ mb: 0.5 }}>{children}</Typography>,
                    a: ({ node, children, ...props }) => <Typography component="a" color="primary" sx={{ textDecoration: 'underline' }} href={props.href}>{children}</Typography>,
                }}
            >
                {markdown}
            </ReactMarkdown>
        </Box>
    );
}