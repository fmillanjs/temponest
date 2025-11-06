import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import { prisma } from "./db/client";

export const auth = betterAuth({
  database: prismaAdapter(prisma, {
    provider: "postgresql",
  }),
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // Set to true in production
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day (refresh session)
  },
  secret: process.env.BETTER_AUTH_SECRET || process.env.AUTH_SECRET || "dev-secret-key-change-in-production",
  baseURL: process.env.AUTH_URL || process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  socialProviders: {
    // Add OAuth providers here if needed
  },
  advanced: {
    generateId: () => crypto.randomUUID(),
  },
});

export type Session = typeof auth.$Infer.Session;
