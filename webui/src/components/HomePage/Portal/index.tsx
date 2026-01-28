import React from "react";
import { Grid, Card, CardContent, CardActionArea, Typography, Box } from "@mui/material";
import DirectionsIcon from "@mui/icons-material/Directions";
import { useApp } from "@/context/AppProvider";
import OpenAiIcon from "./OpenAiIcon";
import ChatbotIcon from "./ChatbotIcon";


interface PortalProps {
    setSelectedAPP: (app: string) => void;
}


export default function Portal(props: PortalProps) {
    const { setSelectedAPP } = props;

    const portalItems = [
        {
            title: 'AI Service Platform',
            icon: <OpenAiIcon />,
            description: 'Self-Hosted LLM access',
            onClick: () => setSelectedAPP('openai-platform')
        },
        {
            title: 'RAG Chatbot',
            icon: <ChatbotIcon />,
            description: 'Chatbot with RAG capabilities',
            onClick: () => setSelectedAPP('chatbot')
        },
        {
            title: 'Other Application',
            icon: <DirectionsIcon />,
            description: 'You can add more applications here',
            onClick: () => {}
        }
    ];


    return (
        <Box sx={{ flexGrow: 1, p: 3, width: '100%' }}>
            <Typography variant="h4" gutterBottom>
                Portal
            </Typography>
            <Grid
                container
                spacing={2}
                columns={12}
                size={{ xs: 12, sm: 6, md: 4 }}
                sx={{ mb: (theme) => theme.spacing(2) }}
            >
                {portalItems.map((item, index) => (
                    <Card key={index}>
                        <CardActionArea sx={{ p: 3, textAlign: 'center' }} onClick={item.onClick}>
                            <Box sx={{ color: 'primary.main', mb: 2 }}>
                                {item.icon}
                            </Box>
                            <CardContent>
                                <Typography variant="h6" component="div" gutterBottom>
                                    {item.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {item.description}
                                </Typography>
                            </CardContent>
                        </CardActionArea>
                    </Card>
                ))}
            </Grid>
        </Box>
    );
}