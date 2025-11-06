/**
 * Permission system for role-based access control
 */

export enum Permission {
  // Project permissions
  PROJECT_CREATE = "project.create",
  PROJECT_EDIT = "project.edit",
  PROJECT_DELETE = "project.delete",
  PROJECT_VIEW = "project.view",

  // Run permissions
  RUN_CREATE = "run.create",
  RUN_CANCEL = "run.cancel",
  RUN_VIEW = "run.view",

  // Agent permissions
  AGENT_CONFIGURE = "agent.configure",
  AGENT_VIEW = "agent.view",

  // Approval permissions
  APPROVAL_APPROVE = "approval.approve",
  APPROVAL_VIEW = "approval.view",

  // Settings permissions
  SETTINGS_EDIT = "settings.edit",
  SETTINGS_VIEW = "settings.view",

  // User permissions
  USER_MANAGE = "user.manage",
  USER_VIEW = "user.view",
}

export type UserRole = "owner" | "collaborator" | "readonly";

/**
 * Map of roles to their permissions
 */
const rolePermissions: Record<UserRole, Permission[]> = {
  owner: [
    // Owners have all permissions
    ...Object.values(Permission),
  ],
  collaborator: [
    // Collaborators can do most things except manage users and some settings
    Permission.PROJECT_CREATE,
    Permission.PROJECT_EDIT,
    Permission.PROJECT_VIEW,
    Permission.RUN_CREATE,
    Permission.RUN_CANCEL,
    Permission.RUN_VIEW,
    Permission.AGENT_VIEW,
    Permission.APPROVAL_APPROVE,
    Permission.APPROVAL_VIEW,
    Permission.SETTINGS_VIEW,
    Permission.USER_VIEW,
  ],
  readonly: [
    // Read-only users can only view things
    Permission.PROJECT_VIEW,
    Permission.RUN_VIEW,
    Permission.AGENT_VIEW,
    Permission.APPROVAL_VIEW,
    Permission.SETTINGS_VIEW,
    Permission.USER_VIEW,
  ],
};

/**
 * Check if a role has a specific permission
 */
export function hasPermission(role: UserRole, permission: Permission): boolean {
  return rolePermissions[role]?.includes(permission) ?? false;
}

/**
 * Check if a role has any of the specified permissions
 */
export function hasAnyPermission(role: UserRole, permissions: Permission[]): boolean {
  return permissions.some((permission) => hasPermission(role, permission));
}

/**
 * Check if a role has all of the specified permissions
 */
export function hasAllPermissions(role: UserRole, permissions: Permission[]): boolean {
  return permissions.every((permission) => hasPermission(role, permission));
}

/**
 * Get all permissions for a role
 */
export function getRolePermissions(role: UserRole): Permission[] {
  return rolePermissions[role] ?? [];
}

/**
 * Check if user can perform write operations
 */
export function canWrite(role: UserRole): boolean {
  return role === "owner" || role === "collaborator";
}

/**
 * Check if user can perform admin operations
 */
export function isAdmin(role: UserRole): boolean {
  return role === "owner";
}
