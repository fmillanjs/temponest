import { StripeService, createStripeService, isStripeConfigured, STRIPE_PLANS } from '../stripe'

// Mock Stripe
const mockStripe = {
  checkout: {
    sessions: {
      create: jest.fn(),
    },
  },
  billingPortal: {
    sessions: {
      create: jest.fn(),
    },
  },
  customers: {
    create: jest.fn(),
    retrieve: jest.fn(),
  },
  subscriptions: {
    retrieve: jest.fn(),
    list: jest.fn(),
    cancel: jest.fn(),
    update: jest.fn(),
  },
  webhooks: {
    constructEvent: jest.fn(),
  },
  invoices: {
    retrieve: jest.fn(),
    list: jest.fn(),
  },
}

// Mock stripe dynamically since it's an optional dependency
jest.mock('stripe', () => ({
  __esModule: true,
  default: jest.fn(() => mockStripe),
}), { virtual: true })

describe('Stripe Service', () => {
  let stripe: StripeService
  const mockConfig = {
    secretKey: 'sk_test_123',
    webhookSecret: 'whsec_123',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    stripe = new StripeService(mockConfig)
  })

  describe('Constructor', () => {
    it('should create service with valid config', () => {
      expect(stripe).toBeInstanceOf(StripeService)
    })

    it('should throw error if secret key is missing', () => {
      expect(() => {
        new StripeService({ secretKey: '' })
      }).toThrow('Stripe secret key is required')
    })

    it('should accept config without webhook secret', () => {
      const service = new StripeService({
        secretKey: 'sk_test_123',
      })

      expect(service).toBeInstanceOf(StripeService)
    })
  })

  describe('createCheckoutSession', () => {
    it('should create checkout session with all parameters', async () => {
      mockStripe.checkout.sessions.create.mockResolvedValue({
        url: 'https://checkout.stripe.com/session_123',
      })

      const result = await stripe.createCheckoutSession({
        organizationId: 'org-123',
        priceId: 'price_123',
        successUrl: 'https://app.example.com/success',
        cancelUrl: 'https://app.example.com/cancel',
        customerId: 'cus_123',
      })

      expect(result).toBe('https://checkout.stripe.com/session_123')
      expect(mockStripe.checkout.sessions.create).toHaveBeenCalledWith({
        customer: 'cus_123',
        line_items: [
          {
            price: 'price_123',
            quantity: 1,
          },
        ],
        mode: 'subscription',
        success_url: 'https://app.example.com/success',
        cancel_url: 'https://app.example.com/cancel',
        metadata: {
          organizationId: 'org-123',
        },
        subscription_data: {
          metadata: {
            organizationId: 'org-123',
          },
        },
      })
    })

    it('should create session without customer ID', async () => {
      mockStripe.checkout.sessions.create.mockResolvedValue({
        url: 'https://checkout.stripe.com/session_456',
      })

      const result = await stripe.createCheckoutSession({
        organizationId: 'org-123',
        priceId: 'price_123',
        successUrl: 'https://app.example.com/success',
        cancelUrl: 'https://app.example.com/cancel',
      })

      expect(result).toBe('https://checkout.stripe.com/session_456')
    })

    it('should return empty string if no URL', async () => {
      mockStripe.checkout.sessions.create.mockResolvedValue({})

      const result = await stripe.createCheckoutSession({
        organizationId: 'org-123',
        priceId: 'price_123',
        successUrl: 'https://app.example.com/success',
        cancelUrl: 'https://app.example.com/cancel',
      })

      expect(result).toBe('')
    })
  })

  describe('createPortalSession', () => {
    it('should create portal session', async () => {
      mockStripe.billingPortal.sessions.create.mockResolvedValue({
        url: 'https://billing.stripe.com/session_789',
      })

      const result = await stripe.createPortalSession({
        customerId: 'cus_123',
        returnUrl: 'https://app.example.com/billing',
      })

      expect(result).toBe('https://billing.stripe.com/session_789')
      expect(mockStripe.billingPortal.sessions.create).toHaveBeenCalledWith({
        customer: 'cus_123',
        return_url: 'https://app.example.com/billing',
      })
    })
  })

  describe('createCustomer', () => {
    it('should create customer with email', async () => {
      mockStripe.customers.create.mockResolvedValue({
        id: 'cus_new123',
      })

      const result = await stripe.createCustomer('user@example.com')

      expect(result).toBe('cus_new123')
      expect(mockStripe.customers.create).toHaveBeenCalledWith({
        email: 'user@example.com',
        metadata: undefined,
      })
    })

    it('should create customer with metadata', async () => {
      mockStripe.customers.create.mockResolvedValue({
        id: 'cus_new456',
      })

      const result = await stripe.createCustomer('user@example.com', {
        organizationId: 'org-123',
        userId: 'user-123',
      })

      expect(result).toBe('cus_new456')
      expect(mockStripe.customers.create).toHaveBeenCalledWith({
        email: 'user@example.com',
        metadata: {
          organizationId: 'org-123',
          userId: 'user-123',
        },
      })
    })
  })

  describe('getCustomer', () => {
    it('should retrieve customer by ID', async () => {
      const mockCustomer = {
        id: 'cus_123',
        email: 'user@example.com',
        name: 'Test User',
      }
      mockStripe.customers.retrieve.mockResolvedValue(mockCustomer)

      const result = await stripe.getCustomer('cus_123')

      expect(result).toEqual(mockCustomer)
      expect(mockStripe.customers.retrieve).toHaveBeenCalledWith('cus_123')
    })
  })

  describe('getSubscription', () => {
    it('should retrieve subscription details', async () => {
      mockStripe.subscriptions.retrieve.mockResolvedValue({
        id: 'sub_123',
        status: 'active',
        current_period_end: 1704067200, // 2024-01-01
        cancel_at_period_end: false,
        items: {
          data: [
            {
              price: {
                id: 'price_123',
              },
            },
          ],
        },
      })

      const result = await stripe.getSubscription('sub_123')

      expect(result).toEqual({
        id: 'sub_123',
        status: 'active',
        currentPeriodEnd: new Date(1704067200 * 1000),
        cancelAtPeriodEnd: false,
        plan: 'price_123',
      })
    })

    it('should return null on error', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
      mockStripe.subscriptions.retrieve.mockRejectedValue(new Error('Not found'))

      const result = await stripe.getSubscription('sub_999')

      expect(result).toBeNull()
      expect(consoleErrorSpy).toHaveBeenCalled()
      consoleErrorSpy.mockRestore()
    })

    it('should handle subscription without items', async () => {
      mockStripe.subscriptions.retrieve.mockResolvedValue({
        id: 'sub_456',
        status: 'canceled',
        current_period_end: 1704067200,
        cancel_at_period_end: false,
        items: {
          data: [],
        },
      })

      const result = await stripe.getSubscription('sub_456')

      expect(result?.plan).toBe('')
    })
  })

  describe('getCustomerSubscriptions', () => {
    it('should list customer subscriptions', async () => {
      mockStripe.subscriptions.list.mockResolvedValue({
        data: [
          {
            id: 'sub_1',
            status: 'active',
            current_period_end: 1704067200,
            cancel_at_period_end: false,
            items: {
              data: [{ price: { id: 'price_123' } }],
            },
          },
          {
            id: 'sub_2',
            status: 'canceled',
            current_period_end: 1704153600,
            cancel_at_period_end: true,
            items: {
              data: [{ price: { id: 'price_456' } }],
            },
          },
        ],
      })

      const result = await stripe.getCustomerSubscriptions('cus_123')

      expect(result).toHaveLength(2)
      expect(result[0].id).toBe('sub_1')
      expect(result[1].id).toBe('sub_2')
      expect(mockStripe.subscriptions.list).toHaveBeenCalledWith({
        customer: 'cus_123',
        status: 'all',
      })
    })

    it('should handle empty subscription list', async () => {
      mockStripe.subscriptions.list.mockResolvedValue({
        data: [],
      })

      const result = await stripe.getCustomerSubscriptions('cus_456')

      expect(result).toEqual([])
    })
  })

  describe('cancelSubscription', () => {
    it('should cancel subscription immediately', async () => {
      mockStripe.subscriptions.cancel.mockResolvedValue({})

      await stripe.cancelSubscription('sub_123', true)

      expect(mockStripe.subscriptions.cancel).toHaveBeenCalledWith('sub_123')
      expect(mockStripe.subscriptions.update).not.toHaveBeenCalled()
    })

    it('should cancel subscription at period end by default', async () => {
      mockStripe.subscriptions.update.mockResolvedValue({})

      await stripe.cancelSubscription('sub_123')

      expect(mockStripe.subscriptions.update).toHaveBeenCalledWith('sub_123', {
        cancel_at_period_end: true,
      })
      expect(mockStripe.subscriptions.cancel).not.toHaveBeenCalled()
    })

    it('should cancel at period end when explicitly set to false', async () => {
      mockStripe.subscriptions.update.mockResolvedValue({})

      await stripe.cancelSubscription('sub_123', false)

      expect(mockStripe.subscriptions.update).toHaveBeenCalledWith('sub_123', {
        cancel_at_period_end: true,
      })
    })
  })

  describe('reactivateSubscription', () => {
    it('should reactivate cancelled subscription', async () => {
      mockStripe.subscriptions.update.mockResolvedValue({})

      await stripe.reactivateSubscription('sub_123')

      expect(mockStripe.subscriptions.update).toHaveBeenCalledWith('sub_123', {
        cancel_at_period_end: false,
      })
    })
  })

  describe('updateSubscriptionPlan', () => {
    it('should update subscription to new plan', async () => {
      mockStripe.subscriptions.retrieve.mockResolvedValue({
        items: {
          data: [{ id: 'si_123' }],
        },
      })
      mockStripe.subscriptions.update.mockResolvedValue({})

      await stripe.updateSubscriptionPlan('sub_123', 'price_new')

      expect(mockStripe.subscriptions.retrieve).toHaveBeenCalledWith('sub_123')
      expect(mockStripe.subscriptions.update).toHaveBeenCalledWith('sub_123', {
        items: [
          {
            id: 'si_123',
            price: 'price_new',
          },
        ],
        proration_behavior: 'always_invoice',
      })
    })
  })

  describe('constructWebhookEvent', () => {
    it('should construct event from webhook', async () => {
      const mockEvent = { type: 'customer.subscription.updated' }
      mockStripe.webhooks.constructEvent.mockReturnValue(mockEvent)

      const result = await stripe.constructWebhookEvent('payload', 'sig_123')

      expect(result).toEqual(mockEvent)
      expect(mockStripe.webhooks.constructEvent).toHaveBeenCalledWith(
        'payload',
        'sig_123',
        'whsec_123'
      )
    })

    it('should throw error if webhook secret not configured', async () => {
      const service = new StripeService({ secretKey: 'sk_test_123' })

      await expect(
        service.constructWebhookEvent('payload', 'sig_123')
      ).rejects.toThrow('Stripe webhook secret not configured')
    })
  })

  describe('getInvoice', () => {
    it('should retrieve invoice by ID', async () => {
      const mockInvoice = {
        id: 'in_123',
        amount_due: 2000,
        currency: 'usd',
      }
      mockStripe.invoices.retrieve.mockResolvedValue(mockInvoice)

      const result = await stripe.getInvoice('in_123')

      expect(result).toEqual(mockInvoice)
      expect(mockStripe.invoices.retrieve).toHaveBeenCalledWith('in_123')
    })
  })

  describe('listCustomerInvoices', () => {
    it('should list customer invoices with default limit', async () => {
      const mockInvoices = {
        data: [
          { id: 'in_1' },
          { id: 'in_2' },
        ],
      }
      mockStripe.invoices.list.mockResolvedValue(mockInvoices)

      const result = await stripe.listCustomerInvoices('cus_123')

      expect(result).toEqual(mockInvoices)
      expect(mockStripe.invoices.list).toHaveBeenCalledWith({
        customer: 'cus_123',
        limit: 10,
      })
    })

    it('should list invoices with custom limit', async () => {
      mockStripe.invoices.list.mockResolvedValue({ data: [] })

      await stripe.listCustomerInvoices('cus_123', 50)

      expect(mockStripe.invoices.list).toHaveBeenCalledWith({
        customer: 'cus_123',
        limit: 50,
      })
    })
  })

  describe('Factory Functions', () => {
    const originalEnv = process.env

    beforeEach(() => {
      jest.resetModules()
      process.env = { ...originalEnv }
    })

    afterAll(() => {
      process.env = originalEnv
    })

    it('should create service from environment variables', () => {
      process.env.STRIPE_SECRET_KEY = 'sk_test_env'

      const service = createStripeService()

      expect(service).toBeInstanceOf(StripeService)
    })

    it('should return null if not configured', () => {
      delete process.env.STRIPE_SECRET_KEY

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
      const service = createStripeService()

      expect(service).toBeNull()
      expect(consoleWarnSpy).toHaveBeenCalled()
      consoleWarnSpy.mockRestore()
    })

    it('should use provided config over environment', () => {
      process.env.STRIPE_SECRET_KEY = 'sk_wrong'

      const service = createStripeService({
        secretKey: 'sk_correct',
      })

      expect(service).toBeInstanceOf(StripeService)
    })

    it('should check if Stripe is configured', () => {
      process.env.STRIPE_SECRET_KEY = 'sk_test_check'

      expect(isStripeConfigured()).toBe(true)
    })

    it('should return false if not configured', () => {
      delete process.env.STRIPE_SECRET_KEY

      expect(isStripeConfigured()).toBe(false)
    })
  })

  describe('STRIPE_PLANS', () => {
    it('should have free plan configuration', () => {
      expect(STRIPE_PLANS.free).toBeDefined()
      expect(STRIPE_PLANS.free.priceId).toBeNull()
      expect(STRIPE_PLANS.free.limits.projects).toBe(1)
    })

    it('should have starter plan configuration', () => {
      expect(STRIPE_PLANS.starter).toBeDefined()
      expect(STRIPE_PLANS.starter.limits.projects).toBe(5)
    })

    it('should have professional plan configuration', () => {
      expect(STRIPE_PLANS.professional).toBeDefined()
      expect(STRIPE_PLANS.professional.limits.projects).toBe(20)
      expect(STRIPE_PLANS.professional.limits.templates).toBe(-1) // unlimited
    })

    it('should have enterprise plan configuration', () => {
      expect(STRIPE_PLANS.enterprise).toBeDefined()
      expect(STRIPE_PLANS.enterprise.limits.projects).toBe(-1) // unlimited
      expect(STRIPE_PLANS.enterprise.limits.members).toBe(-1) // unlimited
    })
  })
})
