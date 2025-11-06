"use client";

import { ReactNode } from "react";
import { usePermissions } from "@/hooks/use-permissions";
import { Permission } from "@/lib/permissions";

interface PermissionGateProps {
  children: ReactNode;
  /** Single permission required */
  permission?: Permission;
  /** Array of permissions - user must have at least one */
  anyPermission?: Permission[];
  /** Array of permissions - user must have all */
  allPermissions?: Permission[];
  /** Require write access (owner or collaborator) */
  canWrite?: boolean;
  /** Require admin access (owner only) */
  isAdmin?: boolean;
  /** Optional fallback component to show if permission denied */
  fallback?: ReactNode;
}

/**
 * Component that conditionally renders children based on user permissions
 *
 * Example usage:
 * ```tsx
 * <PermissionGate permission={Permission.PROJECT_CREATE}>
 *   <Button>Create Project</Button>
 * </PermissionGate>
 *
 * <PermissionGate canWrite>
 *   <EditButton />
 * </PermissionGate>
 *
 * <PermissionGate isAdmin fallback={<ReadOnlyView />}>
 *   <AdminPanel />
 * </PermissionGate>
 * ```
 */
export function PermissionGate({
  children,
  permission,
  anyPermission,
  allPermissions,
  canWrite: requireCanWrite,
  isAdmin: requireIsAdmin,
  fallback = null,
}: PermissionGateProps) {
  const permissions = usePermissions();

  if (permissions.isLoading) {
    return null;
  }

  let hasAccess = true;

  if (permission) {
    hasAccess = permissions.hasPermission(permission);
  } else if (anyPermission) {
    hasAccess = permissions.hasAnyPermission(anyPermission);
  } else if (allPermissions) {
    hasAccess = permissions.hasAllPermissions(allPermissions);
  } else if (requireCanWrite) {
    hasAccess = permissions.canWrite();
  } else if (requireIsAdmin) {
    hasAccess = permissions.isAdmin();
  }

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}
