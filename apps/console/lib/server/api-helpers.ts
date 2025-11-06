import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser, requireAuth, requireRole } from "./session";
import { Permission, hasPermission, type UserRole } from "../permissions";

/**
 * API response helpers
 */
export function jsonResponse(data: any, status = 200) {
  return NextResponse.json(data, { status });
}

export function errorResponse(message: string, status = 400) {
  return NextResponse.json({ error: message }, { status });
}

export function unauthorizedResponse(message = "Unauthorized") {
  return NextResponse.json({ error: message }, { status: 401 });
}

export function forbiddenResponse(message = "Forbidden") {
  return NextResponse.json({ error: message }, { status: 403 });
}

/**
 * Wrapper for API routes that require authentication
 */
export function withAuth(
  handler: (req: NextRequest, context: { user: any }) => Promise<Response>
) {
  return async (req: NextRequest, context: any) => {
    try {
      const user = await requireAuth();
      return await handler(req, { ...context, user });
    } catch (error) {
      return unauthorizedResponse();
    }
  };
}

/**
 * Wrapper for API routes that require specific roles
 */
export function withRole(
  roles: string[],
  handler: (req: NextRequest, context: { user: any }) => Promise<Response>
) {
  return async (req: NextRequest, context: any) => {
    try {
      const user = await requireRole(roles);
      return await handler(req, { ...context, user });
    } catch (error) {
      if (error instanceof Error && error.message === "Unauthorized") {
        return unauthorizedResponse();
      }
      return forbiddenResponse();
    }
  };
}

/**
 * Wrapper for API routes that require specific permissions
 */
export function withPermission(
  permission: Permission,
  handler: (req: NextRequest, context: { user: any }) => Promise<Response>
) {
  return async (req: NextRequest, context: any) => {
    try {
      const user = await requireAuth();

      if (!hasPermission(user.role as UserRole, permission)) {
        return forbiddenResponse("You don't have permission to perform this action");
      }

      return await handler(req, { ...context, user });
    } catch (error) {
      return unauthorizedResponse();
    }
  };
}

/**
 * Rate limiting store (in-memory for now, use Redis in production)
 */
const rateLimitStore = new Map<string, { count: number; resetAt: number }>();

/**
 * Simple rate limiter
 */
export function rateLimit(
  key: string,
  limit: number,
  windowMs: number
): boolean {
  const now = Date.now();
  const record = rateLimitStore.get(key);

  if (!record || now > record.resetAt) {
    rateLimitStore.set(key, {
      count: 1,
      resetAt: now + windowMs,
    });
    return true;
  }

  if (record.count >= limit) {
    return false;
  }

  record.count++;
  return true;
}

/**
 * Wrapper for API routes with rate limiting
 */
export function withRateLimit(
  limit: number,
  windowMs: number,
  handler: (req: NextRequest, context: any) => Promise<Response>
) {
  return async (req: NextRequest, context: any) => {
    const ip = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || "unknown";
    const key = `${ip}:${req.nextUrl.pathname}`;

    if (!rateLimit(key, limit, windowMs)) {
      return NextResponse.json(
        { error: "Too many requests" },
        {
          status: 429,
          headers: {
            "Retry-After": String(Math.ceil(windowMs / 1000)),
          },
        }
      );
    }

    return await handler(req, context);
  };
}

/**
 * Combine multiple middleware wrappers
 */
export function compose(...middlewares: Function[]) {
  return (handler: Function) => {
    return middlewares.reduceRight(
      (acc, middleware) => middleware(acc),
      handler
    );
  };
}

/**
 * Example usage:
 *
 * export const POST = compose(
 *   withAuth,
 *   withPermission(Permission.PROJECT_CREATE),
 *   withRateLimit(10, 60000)
 * )(async (req, { user }) => {
 *   // Your handler code
 * });
 */
