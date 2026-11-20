import { createContext, useContext } from 'react';

// { user, facilities, fid, facility, refreshBadge }
export const AppCtx = createContext(null);
export const useApp = () => useContext(AppCtx);
