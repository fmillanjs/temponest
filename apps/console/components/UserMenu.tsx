"use client";

import { useRouter } from "next/navigation";
import { User, LogOut, Settings, Shield } from "lucide-react";
import { useSession, signOut } from "@/lib/auth-client";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function UserMenu() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const user = session?.user as any;

  const handleSignOut = async () => {
    await signOut();
    router.push("/login");
  };

  if (isPending) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-base-200 bg-white px-3 py-2 text-sm animate-pulse">
        <User className="h-4 w-4" />
        <span>Loading...</span>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "owner":
        return "bg-sky-100 text-sky-700";
      case "collaborator":
        return "bg-emerald-100 text-emerald-700";
      case "readonly":
        return "bg-slate-100 text-slate-700";
      default:
        return "bg-slate-100 text-slate-700";
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-xl border border-base-200 bg-white px-3 py-2 text-sm hover:bg-base-50 focus:outline-none focus:ring-2 focus:ring-accent-info">
          {user.image ? (
            <img src={user.image} alt={user.name || "User"} className="h-6 w-6 rounded-full" />
          ) : (
            <User className="h-4 w-4" />
          )}
          <span className="max-w-[150px] truncate">{user.name || user.email}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.name}</p>
            <p className="text-xs leading-none text-base-500">{user.email}</p>
            <div className="mt-2">
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${getRoleBadgeColor(
                  user.role
                )}`}
              >
                <Shield className="h-3 w-3" />
                {user.role}
              </span>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => router.push("/settings")}>
          <Settings className="mr-2 h-4 w-4" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleSignOut} className="text-rose-600 focus:text-rose-600">
          <LogOut className="mr-2 h-4 w-4" />
          Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
