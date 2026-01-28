'use client';
import React from 'react';
import type { } from '@mui/x-date-pickers/themeAugmentation';
import type { } from '@mui/x-charts/themeAugmentation';
import type { } from '@mui/x-data-grid/themeAugmentation';
import type { } from '@mui/x-tree-view/themeAugmentation';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import AppTheme from '@/theme/AppTheme';
import {
  chartsCustomizations,
  dataGridCustomizations,
} from '@/theme/customizations';
import { UserProvider } from '@/context/UserProvider';
import { AppProvider } from '@/context/AppProvider';
import OpenAiPlatform, { OpenAiPlatformMenuContent } from '@/components/OpenAiPlatform';
import HomePage, { HomePageMenuContent } from '@/components/HomePage';
import Chatbot, { ChatbotMenuContent } from '@/components/Chatbot'
import ViewPort from '@/components/ViewPort';


const xThemeComponents = {
  ...chartsCustomizations,
  ...dataGridCustomizations,
};

const APPLICATION_LIST = [
  {
    value: 'home',
    src: '/static/icon/icons8-home.gif',
    alt: 'Home',
    primary: 'Home',
    secondary: 'Welcome to the home page',
  },
  {
    value: 'openai-platform',
    src: '/static/icon/icons8-chatgpt-96.png',
    alt: 'AI Service Platform',
    primary: 'AI Service Platform',
    secondary: 'Self hosted openai api server',
  },
  {
    value: 'chatbot',
    src: '/static/icon/icons8-chatbot.gif',
    alt: 'RAG Chatbot',
    primary: 'RAG Chatbot',
    secondary: 'Chatbot with RAG capabilities',
  }
]

/**
 * 
 * @param props 
 * @returns 
 */
export default function Dashboard(props: { disableCustomTheme?: boolean }) {
  const [selectedAPP, setSelectedAPP] = React.useState<string>('home');
  const RouteApplication = () => {
    switch (selectedAPP) {
      case 'home':
        return (
          <AppProvider entrypoint='portal'>
            <Box sx={{ display: 'flex' }}>
              <ViewPort
                options={APPLICATION_LIST}
                selectedAPP={selectedAPP}
                setSelectedAPP={setSelectedAPP}
              >
                <HomePageMenuContent />
              </ViewPort>
              <HomePage setSelectedAPP={setSelectedAPP} />
            </Box>
          </AppProvider>
        );
      case 'openai-platform':
        return (
          <AppProvider entrypoint='general' >
            <Box sx={{ display: 'flex' }}>
              <ViewPort
                options={APPLICATION_LIST}
                selectedAPP={selectedAPP}
                setSelectedAPP={setSelectedAPP}
              >
                <OpenAiPlatformMenuContent />
              </ViewPort>
              <OpenAiPlatform />
            </Box>
          </AppProvider>
        );
      case 'chatbot':
        return (
          <AppProvider entrypoint='new_chat' enableChatSession={true} >
            <Box sx={{ display: 'flex' }}>
              <ViewPort
                options={APPLICATION_LIST}
                selectedAPP={selectedAPP}
                setSelectedAPP={setSelectedAPP}
              >
                <ChatbotMenuContent />
              </ViewPort>
              <Chatbot />
            </Box>
          </AppProvider>
        );
      default:
        return null;
    }
  };

  return (
    <UserProvider>
      <AppTheme {...props} themeComponents={xThemeComponents}>
        <CssBaseline enableColorScheme />
        <RouteApplication />
      </AppTheme>
    </UserProvider>
  );
}