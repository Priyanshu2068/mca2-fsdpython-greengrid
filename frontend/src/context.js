import { createContext, useContext } from 'react';

// { user, facilities, fid, facility, refreshBadge }
export const AppCtx = createContext(null);
export const useApp = () => useContext(AppCtx);

/** True when the user is a superuser or has one of the given roles. */
export const hasRole = (user, ...roles) => !!user && (!!user.is_superuser || roles.includes(user.role));
