import { useContext } from "react";
import { AuthContext } from "./AuthContext";
import { login, logout } from "./authStore";

export function useAuth() {
  const auth = useContext(AuthContext);

  if (auth === null) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return {
    ...auth,
    login,
    logout,
  };
}
