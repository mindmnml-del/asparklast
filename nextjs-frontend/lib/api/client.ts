import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from "axios";

// ---------------------------------------------------------------------------
// Custom Error Class
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  isCreditsError: boolean;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.isCreditsError = status === 402;
  }
}

// ---------------------------------------------------------------------------
// Cookie helpers (aispark_token, non-httpOnly, SameSite=Strict, 24h TTL)
// ---------------------------------------------------------------------------

const TOKEN_COOKIE = "aispark_token";
const TOKEN_MAX_AGE = 86400; // 24 hours in seconds

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + TOKEN_COOKIE + "=([^;]*)")
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export function setToken(token: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(
    token
  )}; path=/; max-age=${TOKEN_MAX_AGE}; SameSite=Strict`;
}

export function clearToken(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Strict`;
}

// ---------------------------------------------------------------------------
// Axios Instance
// ---------------------------------------------------------------------------

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60_000,
});

// ---------------------------------------------------------------------------
// Request Interceptor: Inject Bearer token
// ---------------------------------------------------------------------------

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response Interceptor: Handle 401 and 402
// ---------------------------------------------------------------------------

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status;
    const detail =
      error.response?.data?.detail ?? error.message ?? "Unknown error";

    if (status === 401) {
      clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      return Promise.reject(new ApiError(401, detail));
    }

    if (status === 402) {
      return Promise.reject(new ApiError(402, detail));
    }

    return Promise.reject(new ApiError(status ?? 500, detail));
  }
);

export default apiClient;
