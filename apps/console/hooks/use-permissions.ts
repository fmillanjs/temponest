"use client";

import { useSession } from "@/lib/auth-client";
import { Permission, hasPermission, hasAnyPermission, hasAllPermissions, canWrite, isAdmin, type UserRole } from "@/lib/permissions";

/**
 * Hook for checking user permissions
 */
export function usePermissions() {
  const { data: session, isPending } = useSession();
  const userRole = (session?.user as any)?.role as UserRole | undefined;

  return {
    role: userRole,
    isLoading: isPending,
    hasPermission: (permission: Permission) => {
      if (!userRole) return false;
      return hasPermission(userRole, permission);
    },
    hasAnyPermission: (permissions: Permission[]) => {
      if (!userRole) return false;
      return hasAnyPermission(userRole, permissions);
    },
    hasAllPermissions: (permissions: Permission[]) => {
      if (!userRole) return false;
      return hasAllPermissions(userRole, permissions);
    },
    canWrite: () => {
      if (!userRole) return false;
      return canWrite(userRole);
    },
    isAdmin: () => {
      if (!userRole) return false;
      return isAdmin(userRole);
    },
  };
}
