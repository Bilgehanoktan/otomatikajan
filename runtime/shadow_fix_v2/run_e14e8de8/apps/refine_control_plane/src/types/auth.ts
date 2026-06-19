export interface AuthIdentity {
  id: string;
  email: string;
  role?: string | null;
  roles?: string[] | null;
  name?: string;
}

export interface LoginParams {
  email?: string;
  password?: string;
  [key: string]: unknown;
}

export interface RegisterParams {
  email: string;
  password?: string;
  name?: string;
  role?: string;
  [key: string]: unknown;
}

export interface AuthResponse {
  access_token?: string | null;
  operator?: AuthIdentity;
}

export interface AuthActionResult {
  success: boolean;
  redirectTo?: string;
  error?: Error;
}

export type SessionState =
  | { kind: "authenticated"; identity: AuthIdentity }
  | { kind: "unauthorized"; status: number }
  | { kind: "network-error"; error: Error }
  | { kind: "error"; status: number; detail: string };
