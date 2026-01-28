import * as React from 'react';
import MuiAvatar from '@mui/material/Avatar';
import MuiListItemAvatar from '@mui/material/ListItemAvatar';
import MenuItem from '@mui/material/MenuItem';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import Select, { SelectChangeEvent, selectClasses } from '@mui/material/Select';
import { styled } from '@mui/material/styles';
import DevicesRoundedIcon from '@mui/icons-material/DevicesRounded';
import { useApp } from '@/context/AppProvider';


const Avatar = styled(MuiAvatar)(({ theme }) => ({
  width: 28,
  height: 28,
  backgroundColor: (theme.vars || theme).palette.background.paper,
  color: (theme.vars || theme).palette.text.secondary,
  border: `1px solid ${(theme.vars || theme).palette.divider}`,
}));

const ListItemAvatar = styled(MuiListItemAvatar)({
  minWidth: 0,
  marginRight: 12,
});


export type ContentItemProps = {
  value: string;
  src: string;
  alt: string;
  primary: string;
  secondary: string;
}

interface SelectContentProps {
  options: ContentItemProps[];
  selectedAPP: string;
  setSelectedAPP: (value: string) => void;
}

/**
 * SelectContent component
 * @param props - The props for the component
 * @returns The SelectContent component
 */
export default function SelectContent(props: SelectContentProps) {
  const { options, selectedAPP, setSelectedAPP } = props;
  const handleChange = (event: SelectChangeEvent) => {
    setSelectedAPP(event.target.value as string);
  };
  return (
    <Select
      labelId="application-select"
      id="application-simple-select"
      value={selectedAPP || ''}
      onChange={handleChange}
      displayEmpty
      inputProps={{ 'aria-label': 'Select application' }}
      fullWidth
      sx={{
        maxHeight: 56,
        width: 215,
        '&.MuiList-root': {
          p: '8px',
        },
        [`& .${selectClasses.select}`]: {
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
          pl: 1,
        },
      }}
    >
      <ListSubheader sx={{ pt: 0 }}>Production</ListSubheader>

      {options.map((item) => (
        <MenuItem value={item.value}>
          <ListItemAvatar>
            <Avatar
              alt={item.alt}
              src={item.src}
            >
              <DevicesRoundedIcon sx={{ fontSize: '1rem' }} />
            </Avatar>
          </ListItemAvatar>
          <ListItemText primary={item.primary} secondary={item.secondary} />
        </MenuItem>
      ))}
    </Select>
  );
}
