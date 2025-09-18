import { z } from 'zod';
import { createTRPCRouter, protectedProcedure } from '@/server/api/trpc';
import { MovementType } from '@/generated/prisma';

export const inventoryRouter = createTRPCRouter({
  getMovements: protectedProcedure
    .input(
      z.object({
        productId: z.string().optional(),
        type: z.nativeEnum(MovementType).optional(),
        limit: z.number().min(1).max(100).default(50),
        offset: z.number().min(0).default(0),
      })
    )
    .query(async ({ ctx, input }) => {
      const where = {
        organizationId: ctx.organizationId,
        ...(input.productId && { productId: input.productId }),
        ...(input.type && { type: input.type }),
      };

      const [movements, total] = await Promise.all([
        ctx.prisma.inventoryMovement.findMany({
          where,
          include: {
            product: true,
            user: true,
          },
          orderBy: { createdAt: 'desc' },
          take: input.limit,
          skip: input.offset,
        }),
        ctx.prisma.inventoryMovement.count({ where }),
      ]);

      return {
        movements,
        total,
        hasMore: input.offset + input.limit < total,
      };
    }),

  addMovement: protectedProcedure
    .input(
      z.object({
        productId: z.string(),
        type: z.nativeEnum(MovementType),
        quantity: z.number(),
        unitCost: z.number().optional(),
        reference: z.string().optional(),
        notes: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const movement = await ctx.prisma.inventoryMovement.create({
        data: {
          ...input,
          organizationId: ctx.organizationId,
          userId: ctx.session!.user.id,
          totalCost: input.unitCost ? input.quantity * input.unitCost : undefined,
        },
        include: {
          product: true,
        },
      });

      // Update product stock
      const positiveMovements: MovementType[] = [MovementType.PURCHASE, MovementType.ADJUSTMENT];
      const stockChange = positiveMovements.includes(input.type)
        ? input.quantity
        : -Math.abs(input.quantity);

      await ctx.prisma.product.update({
        where: { id: input.productId },
        data: {
          currentStock: {
            increment: stockChange,
          },
        },
      });

      return movement;
    }),
});