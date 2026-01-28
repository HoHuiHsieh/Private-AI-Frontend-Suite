import React from 'react';
import { useUser } from '@/context/UserProvider';
import UserInfoCard from './UserInfoCard';


/**
 * UserCard component displays user information.
 * @returns The rendered UserCard component.
 */
export default function UserCard() {
  const { user } = useUser();

  if (user !== null) {
    return <UserInfoCard user={user!} />
  }
  return null;
}


