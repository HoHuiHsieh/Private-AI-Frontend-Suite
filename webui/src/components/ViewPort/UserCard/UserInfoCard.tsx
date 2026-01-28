import Avatar from '@mui/material/Avatar';
import Stack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { User } from '@/context/UserProvider';
import OptionsMenu from './OptionsMenu';


/**
 * UserCard component displays user information.
 * @returns The rendered UserCard component.
 */
export default function UserInfoCard({ user }: { user: User }) {
  return (
    <Stack
      direction="row"
      sx={{
        p: 2,
        gap: 1,
        alignItems: 'center',
        borderTop: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Avatar
        alt={user?.name ?? ''}
        src={user?.imgsrc ?? ''}
        sx={{ width: 36, height: 36 }}
      />
      <Box sx={{ mr: 'auto' }}>
        <Typography variant="body2" sx={{ fontWeight: 500, lineHeight: '16px' }}>
          {user?.name}
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          {user?.email}
        </Typography>
      </Box>
      <OptionsMenu />
    </Stack>

  );
}


