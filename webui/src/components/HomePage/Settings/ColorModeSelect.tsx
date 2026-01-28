import React from 'react';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import { useColorScheme } from '@mui/material/styles';
import MenuItem from '@mui/material/MenuItem';

const COLOR_MODE_OPTIONS = [
  { label: 'System', value: 'system' },
  { label: 'Light', value: 'light' },
  { label: 'Dark', value: 'dark' },
];

/**
 * Color mode selection select
 * @returns 
 */
export default function ColorModeSelect() {
  // Get the current color mode and a function to change it
  const { mode, setMode } = useColorScheme();
  if (!mode) {
    return null;
  }

  const handleChange = (event: SelectChangeEvent) => {
    setMode(event.target.value as 'light' | 'dark' | 'system');
  };

  return (
    <Select
      value={mode}
      onChange={handleChange}
      sx={{ minWidth: 120 }}
    >
      {COLOR_MODE_OPTIONS.map((option) => (
        <MenuItem key={option.value} value={option.value}>
          {option.label}
        </MenuItem>
      ))}
    </Select>
  );
}


