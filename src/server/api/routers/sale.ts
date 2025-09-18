import { z } from 'zod';
import { createTRPCRouter, protectedProcedure } from '@/server/api/trpc';
import { PaymentMethod } from '@/generated/prisma';

export const saleRouter = createTRPCRouter({
  getAll: protectedProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(100).default(50),
        offset: z.number().min(0).default(0),
        startDate: z.date().optional(),
        endDate: z.date().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      const where = {
        organizationId: ctx.organizationId,
        ...(input.startDate && input.endDate && {
          createdAt: {
            gte: input.startDate,
            lte: input.endDate,
          },
        }),
      };

      const [sales, total] = await Promise.all([
        ctx.prisma.sale.findMany({
          where,
          include: {
            customer: true,
            user: true,
            items: {
              include: {
                product: true,
              },
            },
          },
          orderBy: { createdAt: 'desc' },
          take: input.limit,
          skip: input.offset,
        }),
        ctx.prisma.sale.count({ where }),
      ]);

      return {
        sales,
        total,
        hasMore: input.offset + input.limit < total,
      };
    }),

  create: protectedProcedure
    .input(
      z.object({
        customerId: z.string().optional(),
        items: z.array(
          z.object({
            productId: z.string(),
            quantity: z.number().min(1),
            unitPrice: z.number().min(0),
            discount: z.number().min(0).default(0),
          })
        ),
        paymentMethod: z.nativeEnum(PaymentMethod),
        discount: z.number().min(0).default(0),
        notes: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { items, ...saleData } = input;

      const subtotal = items.reduce(
        (sum, item) => sum + item.quantity * item.unitPrice - item.discount,
        0
      );
      const tax = subtotal * 0.16; // 16% IVA for Mexico
      const total = subtotal + tax - saleData.discount;

      const invoiceNumber = `INV-${Date.now()}`;

      const sale = await ctx.prisma.sale.create({
        data: {
          ...saleData,
          organizationId: ctx.organizationId,
          userId: ctx.session!.user.id,
          invoiceNumber,
          subtotal,
          tax,
          total,
          paidAmount: total,
          items: {
            create: items.map((item) => ({
              ...item,
              total: item.quantity * item.unitPrice - item.discount,
            })),
          },
        },
        include: {
          customer: true,
          items: {
            include: {
              product: true,
            },
          },
        },
      });

      return sale;
    }),
});