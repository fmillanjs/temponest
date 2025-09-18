import { createTRPCRouter } from '@/server/api/trpc';
import { organizationRouter } from './routers/organization';
import { productRouter } from './routers/product';
import { saleRouter } from './routers/sale';
import { customerRouter } from './routers/customer';
import { inventoryRouter } from './routers/inventory';

export const appRouter = createTRPCRouter({
  organization: organizationRouter,
  product: productRouter,
  sale: saleRouter,
  customer: customerRouter,
  inventory: inventoryRouter,
});

export type AppRouter = typeof appRouter;