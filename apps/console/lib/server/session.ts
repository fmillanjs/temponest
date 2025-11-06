import { cookies } from "next/headers";
import { cache } from "react";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db/client";

/**
 * Get the current session from the auth system
 * Cached per request using React cache
 */
export const getSession = cache(async () => {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get("better-auth.session_token");

  if (!sessionToken) {
    return null;
  }

  try {
    const session = await auth.api.getSession({
      headers: {
        cookie: `better-auth.session_token=${sessionToken.value}`,
      },
    });

    return session;
  } catch (error) {
    console.error("Failed to get session:", error);
    return null;
  }
});

/**
 * Get the current user with full details including role
 */
export const getCurrentUser = cache(async () => {
  const session = await getSession();

  if (!session?.user) {
    return null;
  }

  try {
    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        image: true,
        emailVerified: true,
        createdAt: true,
      },
    });

    return user;
  } catch (error) {
    console.error("Failed to get user:", error);
    return null;
  }
});

/**
 * Require authentication - throws if not authenticated
 */
export async function requireAuth() {
  const user = await getCurrentUser();

  if (!user) {
    throw new Error("Unauthorized");
  }

  return user;
}

/**
 * Check if user has required role
 */
export async function hasRole(requiredRoles: string[]) {
  const user = await getCurrentUser();

  if (!user) {
    return false;
  }

  return requiredRoles.includes(user.role);
}

/**
 * Require specific role - throws if user doesn't have role
 */
export async function requireRole(requiredRoles: string[]) {
  const user = await requireAuth();

  if (!requiredRoles.includes(user.role)) {
    throw new Error("Forbidden");
  }

  return user;
}
