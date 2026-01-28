import * as React from 'react';
import { styled } from '@mui/material/styles';
import { grey } from '@mui/material/colors';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import SwipeableDrawer from '@mui/material/SwipeableDrawer';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import OutlinedInput from '@mui/material/OutlinedInput';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import { Theme, useTheme } from '@mui/material/styles';
import { chatbotApi } from '@/services/chatbot';
import { DEFAULT_SYSTEM_PROMPT } from './model';


// Interfaces 
export interface ChatConfig {
  model: string;
  embedding: string;
  system_prompt: string;
  temperature: number;
  top_p: number;
  collections: string[];
}

interface ConfigDrawerProps {
  open: boolean;
  value: ChatConfig;
  onOpen: () => void;
  onClose: () => void;
  onChange: React.Dispatch<React.SetStateAction<ChatConfig>>;
  disableSwipeToOpen?: boolean;
}

// Styles
const StyledBox = styled('div')(({ theme }) => ({
  backgroundColor: '#fff',
  ...theme.applyStyles('dark', {
    backgroundColor: grey[800],
  }),
}));

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

function getStyles(name: string, personName: readonly string[], theme: Theme) {
  return {
    fontWeight: personName.includes(name)
      ? theme.typography.fontWeightMedium
      : theme.typography.fontWeightRegular,
  };
}

/**
 * ConfigDrawer component - A swipeable drawer for displaying chat results
 * @param props - Component props
 * @returns ConfigDrawer component
 */
export default function ConfigDrawer(props: ConfigDrawerProps) {
  const { open, onOpen, value, onChange, onClose, disableSwipeToOpen = false } = props;
  const theme = useTheme();

  // Load system_prompt from localStorage on mount
  React.useEffect(() => {
    const savedPrompt = localStorage.getItem('system_prompt');
    if (savedPrompt) {
      onChange((state) => ({ ...state, system_prompt: savedPrompt }));
    }
  }, [onChange]);

  // Save system_prompt to localStorage when it changes
  React.useEffect(() => {
    localStorage.setItem('system_prompt', value.system_prompt);
  }, [value.system_prompt]);

  // Handle config value
  const handleChange = (field: keyof ChatConfig, value: any) => {
    onChange((state) => ({ ...state, [field]: value }));
  };
  const handleClose = () => onClose();

  // Fetch model list
  const [models, setModels] = React.useState<any>(null);
  React.useEffect(() => {
    const fetchModels = async () => {
      const modelList = await chatbotApi.getModelList();
      setModels(modelList.data);
      onChange((state) => ({
        ...state,
        "model": state.model || modelList.data.chat[0] || '',
        "embedding": state.embedding || modelList.data.embedding[0] || '',
        "collections": state.collections || modelList.data.collections || [],
      }));
    };
    console.log("Fetching models...");

    fetchModels();
  }, []);

  // Check if models are loaded
  if (!models) {
    return null;
  }

  return (
    <div inert={!open ? true : undefined}>
      <SwipeableDrawer
        anchor="right"
        open={open}
        onClose={() => handleClose()}
        onOpen={() => onOpen()}
        disableSwipeToOpen={disableSwipeToOpen}
        ModalProps={{
          keepMounted: true,
        }}
        slotProps={{
          paper: { sx: { width: 320 } }
        }}
      >
        <StyledBox sx={{ px: 4, pb: 4, height: '100%', overflow: 'auto', }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Chat Configuration</Typography>
          <TextField
            label="System Prompt"
            multiline
            minRows={8}
            fullWidth
            value={value.system_prompt}
            onChange={(e) => handleChange('system_prompt', e.target.value)}
            slotProps={{
              inputLabel: { shrink: true },
              input: { sx: { overflowY: 'auto' } },
            }}
            sx={{ mb: 2, '& .MuiOutlinedInput-root': { minHeight: '240px' } }}
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel shrink>Model</InputLabel>
            <Select
              value={value.model}
              label="Model"
              onChange={(e) => handleChange('model', e.target.value)}
            >
              {models.chat.map((item) => (
                <MenuItem key={item} value={item}>{item}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel shrink>Embedding</InputLabel>
            <Select
              value={value.embedding}
              label="Embedding"
              onChange={(e) => handleChange('embedding', e.target.value)}
            >
              {models.embedding.map((item) => (
                <MenuItem key={item} value={item}>{item}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Temperature"
            type="number"
            fullWidth
            value={value.temperature}
            onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            slotProps={{
              htmlInput: { min: 0, max: 2, step: 0.1 },
              inputLabel: { shrink: true },
            }}
            sx={{ mb: 2 }}
          />

          <TextField
            label="Top P"
            type="number"
            fullWidth
            value={value.top_p}
            onChange={(e) => handleChange('top_p', parseFloat(e.target.value))}
            slotProps={{
              htmlInput: { min: 0, max: 2, step: 0.1 },
              inputLabel: { shrink: true },
            }}
            sx={{ mb: 2 }}
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="multiple-collections-label">Collections</InputLabel>
            <Select
              labelId="multiple-collections-label"
              id="multiple-collections"
              multiple
              value={value.collections}
              onChange={(e) => handleChange('collections', e.target.value)}
              input={<OutlinedInput id="select-multiple-chip" label="Collections" sx={{ height: 'auto', minHeight: '56px' }} />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} />
                  ))}
                </Box>
              )}
              MenuProps={MenuProps}
            >
              {models.collections.map((name) => (
                <MenuItem
                  key={name}
                  value={name}
                  style={getStyles(name, value.collections, theme)}
                >
                  {name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

        </StyledBox>
      </SwipeableDrawer>
    </div>
  );
}
