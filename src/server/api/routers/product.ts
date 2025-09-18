import { z } from 'zod';
import { createTRPCRouter, protectedProcedure } from '@/server/api/trpc';

export const productRouter = createTRPCRouter({
  getAll: protectedProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(100).default(50),
        offset: z.number().min(0).default(0),
        search: z.string().optional(),
        categoryId: z.string().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      const where = {
        organizationId: ctx.organizationId,
        isActive: true,
        ...(input.search && {
          OR: [
            { name: { contains: input.search, mode: 'insensitive' as const } },
            { sku: { contains: input.search, mode: 'insensitive' as const } },
            { barcode: { contains: input.search, mode: 'insensitive' as const } },
          ],
        }),
        ...(input.categoryId && { categoryId: input.categoryId }),
      };

      const [products, total] = await Promise.all([
        ctx.prisma.product.findMany({
          where,
          include: {
            category: true,
          },
          orderBy: { name: 'asc' },
          take: input.limit,
          skip: input.offset,
        }),
        ctx.prisma.product.count({ where }),
      ]);

      return {
        products,
        total,
        hasMore: input.offset + input.limit < total,
      };
    }),

  create: protectedProcedure
    .input(
      z.object({
        sku: z.string().min(1),
        name: z.string().min(1),
        description: z.string().optional(),
        categoryId: z.string().optional(),
        barcode: z.string().optional(),
        costPrice: z.number().min(0),
        salePrice: z.number().min(0),
        minStock: z.number().min(0).default(0),
        maxStock: z.number().min(0).optional(),
        unit: z.string().default('pcs'),
        expirationDate: z.date().optional(),
        batch: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const product = await ctx.prisma.product.create({
        data: {
          ...input,
          organizationId: ctx.organizationId,
        },
        include: {
          category: true,
        },
      });

      return product;
    }),
});