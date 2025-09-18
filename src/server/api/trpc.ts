import { initTRPC, TRPCError } from '@trpc/server';
import { type CreateNextContextOptions } from '@trpc/server/adapters/next';
import { type Session } from 'next-auth';
import { getServerSession } from 'next-auth/next';
import superjson from 'superjson';
import { ZodError } from 'zod';
import { PrismaClient } from '@/generated/prisma';
import { authOptions } from '@/server/auth';

const prisma = new PrismaClient();

type CreateContextOptions = {
  session: Session | null;
};

const createInnerTRPCContext = (opts: CreateContextOptions) => {
  return {
    session: opts.session,
    prisma,
  };
};

export const createTRPCContext = async (opts: CreateNextContextOptions) => {
  const { req, res } = opts;

  const session = await getServerSession(req, res, authOptions);

  return createInnerTRPCContext({
    session,
  });
};

const t = initTRPC.context<typeof createTRPCContext>().create({
  transformer: superjson,
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        zodError:
          error.cause instanceof ZodError ? error.cause.flatten() : null,
      },
    };
  },
});

export const createTRPCRouter = t.router;

export const publicProcedure = t.procedure;

const enforceUserIsAuthed = t.middleware(({ ctx, next }) => {
  if (!ctx.session || !ctx.session.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next({
    ctx: {
      session: { ...ctx.session, user: ctx.session.user },
    },
  });
});

const enforceOrganizationAccess = t.middleware(({ ctx, next }) => {
  if (!ctx.session?.user?.organizationId) {
    throw new TRPCError({
      code: 'FORBIDDEN',
      message: 'User must belong to an organization'
    });
  }
  return next({
    ctx: {
      ...ctx,
      organizationId: ctx.session.user.organizationId,
    },
  });
});

export const protectedProcedure = t.procedure
  .use(enforceUserIsAuthed)
  .use(enforceOrganizationAccess);