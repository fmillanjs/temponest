import { type RouterOutputs } from '@/utils/api';

// Organization types
export type Organization = RouterOutputs['organization']['getCurrent'];
export type OrganizationWithCounts = Organization & {
  _count: {
    users: number;
    products: number;
    customers: number;
  };
};

// Product types
export type Product = RouterOutputs['product']['getAll']['products'][0];
export type ProductWithCategory = Product & {
  category: {
    id: string;
    name: string;
  } | null;
};

// Sale types
export type Sale = RouterOutputs['sale']['getAll']['sales'][0];
export type SaleWithDetails = Sale & {
  customer: {
    id: string;
    name: string;
    phone: string | null;
  } | null;
  user: {
    id: string;
    name: string;
  };
  items: Array<{
    id: string;
    quantity: number;
    unitPrice: number;
    discount: number;
    total: number;
    product: {
      id: string;
      name: string;
      sku: string;
    };
  }>;
};

// Customer types
export type Customer = RouterOutputs['customer']['getAll']['customers'][0];

// Inventory types
export type InventoryMovement = RouterOutputs['inventory']['getMovements']['movements'][0];

// Dashboard types
export interface DashboardStats {
  totalSales: number;
  totalProducts: number;
  totalCustomers: number;
  lowStockProducts: number;
  todaySales: number;
  monthSales: number;
}

export interface SalesChartData {
  date: string;
  sales: number;
  profit: number;
}

// Form types for mutations
export interface CreateProductForm {
  sku: string;
  name: string;
  description?: string;
  categoryId?: string;
  barcode?: string;
  costPrice: number;
  salePrice: number;
  minStock: number;
  maxStock?: number;
  unit: string;
  expirationDate?: Date;
  batch?: string;
}

export interface CreateSaleForm {
  customerId?: string;
  items: Array<{
    productId: string;
    quantity: number;
    unitPrice: number;
    discount: number;
  }>;
  paymentMethod: 'CASH' | 'CARD' | 'TRANSFER' | 'CREDIT';
  discount: number;
  notes?: string;
}

export interface CreateCustomerForm {
  name: string;
  phone?: string;
  whatsappPhone?: string;
  email?: string;
  address?: string;
  creditLimit: number;
  notes?: string;
}