import { getCurrentUser, loginUser, logoutUser } from "../services/authService";

let state = {
  user: null,
  loading: true,
};

const listeners = new Set();

function getSnapshot() {
  return state;
}

function subscribe(listener) {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

function setState(nextState) {
  state = nextState;
  listeners.forEach((listener) => listener());
}

async function initializeAuth() {
  try {
    const currentUser = await getCurrentUser();

    setState({
      user: currentUser,
      loading: false,
    });
  } catch {
    setState({
      user: null,
      loading: false,
    });
  }
}

async function login(credentials) {
  const loggedInUser = await loginUser(credentials);

  setState({
    user: loggedInUser,
    loading: false,
  });

  return loggedInUser;
}

async function logout() {
  await logoutUser();

  setState({
    user: null,
    loading: false,
  });
}

initializeAuth();

export { getSnapshot, subscribe, login, logout };
