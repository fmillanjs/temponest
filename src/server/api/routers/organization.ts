import { z } from 'zod';
import { createTRPCRouter, protectedProcedure, publicProcedure } from '@/server/api/trpc';
import { SubscriptionPlan, SubscriptionStatus } from '@/generated/prisma';

export const organizationRouter = createTRPCRouter({
  getCurrent: protectedProcedure.query(async ({ ctx }) => {
    const organization = await ctx.prisma.organization.findUnique({
      where: { id: ctx.organizationId },
      include: {
        subscription: true,
        _count: {
          select: {
            users: true,
            products: true,
            customers: true,
          },
        },
      },
    });

    if (!organization) {
      throw new Error('Organization not found');
    }

    return organization;
  }),

  create: publicProcedure
    .input(
      z.object({
        name: z.string().min(1),
        whatsappPhone: z.string().min(10),
        rfc: z.string().optional(),
        address: z.string().optional(),
        phone: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const organization = await ctx.prisma.organization.create({
        data: {
          ...input,
          subscription: {
            create: {
              plan: SubscriptionPlan.BASIC,
              status: SubscriptionStatus.TRIAL,
              startDate: new Date(),
              trialEndsAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
            },
          },
        },
        include: {
          subscription: true,
        },
      });

      return organization;
    }),

  update: protectedProcedure
    .input(
      z.object({
        name: z.string().min(1).optional(),
        rfc: z.string().optional(),
        address: z.string().optional(),
        phone: z.string().optional(),
        whatsappPhone: z.string().min(10).optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const organization = await ctx.prisma.organization.update({
        where: { id: ctx.organizationId },
        data: input,
      });

      return organization;
    }),

  getSubscription: protectedProcedure.query(async ({ ctx }) => {
    const subscription = await ctx.prisma.subscription.findUnique({
      where: { organizationId: ctx.organizationId },
    });

    return subscription;
  }),
});