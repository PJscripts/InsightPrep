import { createContext } from "react";
import { useSyncExternalStore } from "react";
import { getSnapshot, subscribe } from "./authStore";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const auth = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

export { AuthContext };
