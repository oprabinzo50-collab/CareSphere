import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { getMe, type AuthUser } from "../api/auth";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  loginUser: (token: string, nextUser: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<
  AuthContextValue | undefined
>(undefined);

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    let mounted = true;

    const token =
      sessionStorage.getItem(
        "caresphere_token",
      );

    if (!token) {
      if (mounted) {
        setLoading(false);
      }

      return () => {
        mounted = false;
      };
    }

    getMe()
      .then((sessionUser) => {
        if (mounted) {
          setUser(sessionUser);
        }
      })
      .catch(() => {
        sessionStorage.removeItem(
          "caresphere_token",
        );

        sessionStorage.removeItem(
          "caresphere_user",
        );

        localStorage.removeItem(
          "caresphere_token",
        );

        localStorage.removeItem(
          "caresphere_user",
        );

        if (mounted) {
          setUser(null);
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,

      loginUser: (
        token,
        nextUser,
      ) => {
        sessionStorage.setItem(
          "caresphere_token",
          token,
        );

        sessionStorage.setItem(
          "caresphere_user",
          JSON.stringify(nextUser),
        );

        setUser(nextUser);
      },

      logout: () => {
        sessionStorage.removeItem(
          "caresphere_token",
        );

        sessionStorage.removeItem(
          "caresphere_user",
        );

        localStorage.removeItem(
          "caresphere_token",
        );

        localStorage.removeItem(
          "caresphere_user",
        );

        setUser(null);
      },
    }),
    [user, loading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}