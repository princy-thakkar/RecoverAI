import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  API_BASE_URL,
  API_ENDPOINTS,
} from '@/config/env';


/* =========================================================
   TYPES
========================================================= */

export type AuthUser = {
  id?: string;
  email: string;
  name?: string;
  role?: string;
};


type LoginResponse = {
  access_token?: string;
  token?: string;
  user?: AuthUser;
  success?: boolean;
  detail?: string;
};


type RequestDemoResponse = {
  success: boolean;
  message?: string;
  user?: AuthUser;
  access_token?: string;
  token?: string;
  detail?: string;
};


type ErrorResponse = {
  detail?: string;
};


type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  authenticated: boolean;

  login: (
    email: string,
    password: string,
  ) => Promise<void>;

  requestDemo: (
    name: string,
    email: string,
    businessName: string,
    password: string,
    confirmPassword: string,
  ) => Promise<void>;

  logout: () => void;
};


/* =========================================================
   STORAGE KEYS
========================================================= */

const TOKEN_KEY = 'recoverai_access_token';
const USER_KEY = 'recoverai_user';


/* =========================================================
   HELPERS
========================================================= */

function isValidUser(
  value: unknown,
): value is AuthUser {

  if (
    !value ||
    typeof value !== 'object'
  ) {
    return false;
  }

  const candidate =
    value as Partial<AuthUser>;

  return (
    typeof candidate.email === 'string' &&
    candidate.email.trim().length > 0
  );
}


function getStoredUser(): AuthUser | null {

  const stored =
    localStorage.getItem(USER_KEY);

  if (!stored) {
    return null;
  }

  try {

    const parsed =
      JSON.parse(stored);

    if (!isValidUser(parsed)) {

      localStorage.removeItem(
        USER_KEY,
      );

      return null;
    }

    return parsed;

  } catch {

    localStorage.removeItem(
      USER_KEY,
    );

    return null;
  }
}


function getAccessToken(
  body:
    | LoginResponse
    | RequestDemoResponse,
): string | null {

  const accessToken =
    body.access_token ??
    body.token;

  if (
    typeof accessToken !== 'string' ||
    !accessToken.trim()
  ) {
    return null;
  }

  return accessToken;
}


async function parseResponse<T>(
  response: Response,
): Promise<T | ErrorResponse> {

  try {

    return (
      await response.json()
    ) as T;

  } catch {

    return {};
  }
}


function getErrorMessage(
  body: ErrorResponse,
  fallback: string,
): string {

  return (
    typeof body.detail === 'string' &&
    body.detail.trim()
      ? body.detail
      : fallback
  );
}


/* =========================================================
   CONTEXT
========================================================= */

const AuthContext =
  createContext<
    AuthContextValue | undefined
  >(undefined);


/* =========================================================
   PROVIDER
========================================================= */

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {

  const [token, setToken] =
    useState<string | null>(() =>
      localStorage.getItem(TOKEN_KEY),
    );


  const [user, setUser] =
    useState<AuthUser | null>(
      getStoredUser,
    );


  const [loading, setLoading] =
    useState(true);


  /* =======================================================
     CLEAR AUTHENTICATION
  ======================================================= */

  const clearAuthentication =
    useCallback(() => {

      localStorage.removeItem(
        TOKEN_KEY,
      );

      localStorage.removeItem(
        USER_KEY,
      );

      setToken(null);
      setUser(null);

    }, []);


  /* =======================================================
     LOGOUT
  ======================================================= */

  const logout =
    useCallback(() => {

      clearAuthentication();

    }, [
      clearAuthentication,
    ]);


  /* =======================================================
     LOGIN
  ======================================================= */

  const login =
    useCallback(
      async (
        email: string,
        password: string,
      ) => {

        const cleanEmail =
          email.trim().toLowerCase();


        if (!cleanEmail) {

          throw new Error(
            'Please enter your email address.',
          );
        }


        if (!password) {

          throw new Error(
            'Please enter your password.',
          );
        }


        const response =
          await fetch(
            `${API_BASE_URL}${API_ENDPOINTS.login}`,
            {
              method: 'POST',

              headers: {
                'Content-Type':
                  'application/json',
              },

              body: JSON.stringify({
                email: cleanEmail,
                password,
              }),
            },
          );


        const body =
          await parseResponse<
            LoginResponse
          >(response);


        if (!response.ok) {

          throw new Error(
            getErrorMessage(
              body as ErrorResponse,
              'Invalid email or password.',
            ),
          );
        }


        const accessToken =
          getAccessToken(
            body as LoginResponse,
          );


        if (!accessToken) {

          throw new Error(
            'Login succeeded but the server did not return an access token.',
          );
        }


        /* -----------------------------------------------
           GET USER FROM LOGIN RESPONSE
        ------------------------------------------------ */

        let authenticatedUser =
          isValidUser(
            (body as LoginResponse).user,
          )
            ? (body as LoginResponse).user
            : undefined;


        /* -----------------------------------------------
           FALL BACK TO /ME
        ------------------------------------------------ */

        if (!authenticatedUser) {

          const meResponse =
            await fetch(
              `${API_BASE_URL}${API_ENDPOINTS.me}`,
              {
                method: 'GET',

                headers: {
                  Authorization:
                    `Bearer ${accessToken}`,
                },
              },
            );


          if (!meResponse.ok) {

            clearAuthentication();

            throw new Error(
              'Unable to retrieve the authenticated user.',
            );
          }


          const meBody =
            await parseResponse<AuthUser>(
              meResponse,
            );


          if (
            !isValidUser(meBody)
          ) {

            clearAuthentication();

            throw new Error(
              'The server did not return valid authenticated user information.',
            );
          }


          authenticatedUser =
            meBody;
        }


        /* -----------------------------------------------
           STORE AUTHENTICATION
        ------------------------------------------------ */

        localStorage.setItem(
          TOKEN_KEY,
          accessToken,
        );

        localStorage.setItem(
          USER_KEY,
          JSON.stringify(
            authenticatedUser,
          ),
        );


        setToken(
          accessToken,
        );

        setUser(
          authenticatedUser,
        );

      },
      [
        clearAuthentication,
      ],
    );


  /* =======================================================
     REQUEST DEMO / CREATE ACCOUNT
  ======================================================= */

  const requestDemo =
    useCallback(
      async (
        name: string,
        email: string,
        businessName: string,
        password: string,
        confirmPassword: string,
      ) => {

        const cleanName =
          name.trim();

        const cleanEmail =
          email.trim().toLowerCase();

        const cleanBusinessName =
          businessName.trim();


        /* -----------------------------------------------
           CLIENT-SIDE VALIDATION
        ------------------------------------------------ */

        if (!cleanName) {

          throw new Error(
            'Please enter your name.',
          );
        }


        if (!cleanEmail) {

          throw new Error(
            'Please enter your email address.',
          );
        }


        if (!cleanBusinessName) {

          throw new Error(
            'Please enter your business name.',
          );
        }


        if (!password) {

          throw new Error(
            'Please create a password.',
          );
        }


        if (password.length < 8) {

          throw new Error(
            'Password must be at least 8 characters.',
          );
        }


        if (!confirmPassword) {

          throw new Error(
            'Please confirm your password.',
          );
        }


        if (
          password !==
          confirmPassword
        ) {

          throw new Error(
            'Passwords do not match.',
          );
        }


        /* -----------------------------------------------
           CREATE ACCOUNT
        ------------------------------------------------ */

        const response =
          await fetch(
            `${API_BASE_URL}${API_ENDPOINTS.requestDemo}`,
            {
              method: 'POST',

              headers: {
                'Content-Type':
                  'application/json',
              },

              body: JSON.stringify({
                name: cleanName,
                email: cleanEmail,
                business_name:
                  cleanBusinessName,
                password,
                confirm_password:
                  confirmPassword,
              }),
            },
          );


        const body =
          await parseResponse<
            RequestDemoResponse
          >(response);


        if (!response.ok) {

          throw new Error(
            getErrorMessage(
              body as ErrorResponse,
              'Unable to create your RecoverAI account.',
            ),
          );
        }


        const accessToken =
          getAccessToken(
            body as RequestDemoResponse,
          );


        if (!accessToken) {

          throw new Error(
            'Account was created but the server did not return an access token.',
          );
        }


        /* -----------------------------------------------
           GET USER FROM RESPONSE
        ------------------------------------------------ */

        let authenticatedUser =
          isValidUser(
            (body as RequestDemoResponse).user,
          )
            ? (body as RequestDemoResponse).user
            : undefined;


        /* -----------------------------------------------
           FALL BACK TO /ME
        ------------------------------------------------ */

        if (!authenticatedUser) {

          const meResponse =
            await fetch(
              `${API_BASE_URL}${API_ENDPOINTS.me}`,
              {
                method: 'GET',

                headers: {
                  Authorization:
                    `Bearer ${accessToken}`,
                },
              },
            );


          if (!meResponse.ok) {

            clearAuthentication();

            throw new Error(
              'Account was created but authentication could not be completed.',
            );
          }


          const meBody =
            await parseResponse<AuthUser>(
              meResponse,
            );


          if (
            !isValidUser(meBody)
          ) {

            clearAuthentication();

            throw new Error(
              'Account was created but the authenticated user could not be verified.',
            );
          }


          authenticatedUser =
            meBody;
        }


        /* -----------------------------------------------
           STORE AUTHENTICATION
        ------------------------------------------------ */

        localStorage.setItem(
          TOKEN_KEY,
          accessToken,
        );

        localStorage.setItem(
          USER_KEY,
          JSON.stringify(
            authenticatedUser,
          ),
        );


        setToken(
          accessToken,
        );

        setUser(
          authenticatedUser,
        );

      },
      [
        clearAuthentication,
      ],
    );


  /* =======================================================
     RESTORE AUTHENTICATION
  ======================================================= */

  useEffect(() => {

    let cancelled = false;


    const restoreAuthentication =
      async () => {

        const storedToken =
          localStorage.getItem(
            TOKEN_KEY,
          );


        /* ---------------------------------------------
           NO STORED TOKEN
        --------------------------------------------- */

        if (!storedToken) {

          if (!cancelled) {

            setToken(null);
            setUser(null);
            setLoading(false);

          }

          return;
        }


        try {

          const response =
            await fetch(
              `${API_BASE_URL}${API_ENDPOINTS.me}`,
              {
                method: 'GET',

                headers: {
                  Authorization:
                    `Bearer ${storedToken}`,
                },
              },
            );


          /* -------------------------------------------
             TOKEN EXPIRED / INVALID
          ------------------------------------------- */

          if (
            response.status === 401
          ) {

            if (!cancelled) {
              clearAuthentication();
            }

            return;
          }


          if (!response.ok) {

            throw new Error(
              `Authentication restore failed: ${response.status}`,
            );
          }


          const body =
            await parseResponse<AuthUser>(
              response,
            );


          if (
            !isValidUser(body)
          ) {

            throw new Error(
              'Authenticated user response was invalid.',
            );
          }


          localStorage.setItem(
            USER_KEY,
            JSON.stringify(body),
          );


          if (!cancelled) {

            setToken(
              storedToken,
            );

            setUser(
              body,
            );

          }

        } catch (error) {

          console.error(
            'Unable to restore authentication:',
            error,
          );


          if (!cancelled) {
            clearAuthentication();
          }

        } finally {

          if (!cancelled) {
            setLoading(false);
          }

        }
      };


    void restoreAuthentication();


    return () => {
      cancelled = true;
    };

  }, [
    clearAuthentication,
  ]);


  /* =======================================================
     CONTEXT VALUE
  ======================================================= */

  const value =
    useMemo<AuthContextValue>(
      () => ({
        user,
        token,
        loading,

        authenticated:
          Boolean(
            token &&
            user,
          ),

        login,
        requestDemo,
        logout,
      }),

      [
        user,
        token,
        loading,
        login,
        requestDemo,
        logout,
      ],
    );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}


/* =========================================================
   USE AUTH
========================================================= */

export function useAuth() {

  const context =
    useContext(
      AuthContext,
    );


  if (!context) {

    throw new Error(
      'useAuth must be used inside AuthProvider.',
    );

  }


  return context;
}