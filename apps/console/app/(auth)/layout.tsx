import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In - SaaS Empire Console",
  description: "Sign in to manage your autonomous SaaS factory",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
