"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import {
  Home,
  Map,
  FolderKanban,
  Folder,
  Users,
  Wand2,
  Calculator,
  FileText,
  Activity,
  Settings,
  LogOut,
  Search,
} from "lucide-react";
import { signOut } from "@/lib/auth-client";

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false);
    command();
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Navigation">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/dashboard"))}
          >
            <Home className="mr-2 h-4 w-4" />
            <span>Dashboard</span>
            <CommandShortcut>⌘D</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/factory-map"))}
          >
            <Map className="mr-2 h-4 w-4" />
            <span>Factory Map</span>
            <CommandShortcut>⌘M</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/workflows"))}
          >
            <FolderKanban className="mr-2 h-4 w-4" />
            <span>Workflows</span>
            <CommandShortcut>⌘W</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/projects"))}
          >
            <Folder className="mr-2 h-4 w-4" />
            <span>Projects</span>
            <CommandShortcut>⌘P</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/agents"))}
          >
            <Users className="mr-2 h-4 w-4" />
            <span>Agents</span>
            <CommandShortcut>⌘A</CommandShortcut>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Tools">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/wizards"))}
          >
            <Wand2 className="mr-2 h-4 w-4" />
            <span>Wizards</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/financials"))}
          >
            <Calculator className="mr-2 h-4 w-4" />
            <span>Financial Calculator</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/docs"))}
          >
            <FileText className="mr-2 h-4 w-4" />
            <span>Documentation</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/observability"))}
          >
            <Activity className="mr-2 h-4 w-4" />
            <span>Observability</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Settings">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/settings"))}
          >
            <Settings className="mr-2 h-4 w-4" />
            <span>Settings</span>
            <CommandShortcut>⌘,</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() =>
              runCommand(async () => {
                await signOut();
                router.push("/login");
              })
            }
          >
            <LogOut className="mr-2 h-4 w-4" />
            <span>Sign Out</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
