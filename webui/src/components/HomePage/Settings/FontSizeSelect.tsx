import React from 'react';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import { useUser } from '@/context/UserProvider';

const FONT_SIZE_OPTIONS = [
  { label: 'Small', value: 'small' },
  { label: 'Medium', value: 'medium' },
  { label: 'Large', value: 'large' },
];

/**
 * Font size selection select
 * @returns 
 */
export default function FontSizeSelect() {
  const { fontSize, setFontSize } = useUser();

  const handleChange = (event: SelectChangeEvent) => {
    setFontSize(event.target.value as 'small' | 'medium' | 'large');
  };

  return (
    <Select
      value={fontSize}
      onChange={handleChange}
      sx={{ minWidth: 120 }}
    >
      {FONT_SIZE_OPTIONS.map((option) => (
        <MenuItem key={option.value} value={option.value}>
          {option.label}
        </MenuItem>
      ))}
    </Select>
  );
}
