import { z } from 'zod';
import { createTRPCRouter, protectedProcedure } from '@/server/api/trpc';

export const customerRouter = createTRPCRouter({
  getAll: protectedProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(100).default(50),
        offset: z.number().min(0).default(0),
        search: z.string().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      const where = {
        organizationId: ctx.organizationId,
        isActive: true,
        ...(input.search && {
          OR: [
            { name: { contains: input.search, mode: 'insensitive' as const } },
            { phone: { contains: input.search, mode: 'insensitive' as const } },
            { email: { contains: input.search, mode: 'insensitive' as const } },
          ],
        }),
      };

      const [customers, total] = await Promise.all([
        ctx.prisma.customer.findMany({
          where,
          orderBy: { name: 'asc' },
          take: input.limit,
          skip: input.offset,
        }),
        ctx.prisma.customer.count({ where }),
      ]);

      return {
        customers,
        total,
        hasMore: input.offset + input.limit < total,
      };
    }),

  create: protectedProcedure
    .input(
      z.object({
        name: z.string().min(1),
        phone: z.string().optional(),
        whatsappPhone: z.string().optional(),
        email: z.string().email().optional(),
        address: z.string().optional(),
        creditLimit: z.number().min(0).default(0),
        notes: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const customer = await ctx.prisma.customer.create({
        data: {
          ...input,
          organizationId: ctx.organizationId,
        },
      });

      return customer;
    }),
});