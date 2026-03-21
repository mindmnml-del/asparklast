import axios, {
  type AxiosError,
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
// Axios Instance — cookies sent automatically via withCredentials
// ---------------------------------------------------------------------------

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60_000,
  withCredentials: true,
});

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
      // Ask the backend to clear the httpOnly cookie
      apiClient.post("/auth/logout").catch(() => {});
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
