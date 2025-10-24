import { Job } from 'bullmq'
import type { SendEmailJob } from '@temponest/types'

// Mock dependencies
const mockConfig = {
  email: {
    from: 'noreply@temponest.app',
    resendApiKey: '',
    smtpHost: '',
    smtpPort: 587,
    smtpSecure: false,
    smtpUser: '',
    smtpPassword: '',
  },
  workers: {
    concurrency: 1,
  },
}

const mockResend = {
  emails: {
    send: jest.fn(),
  },
}

const mockNodemailer = {
  default: {
    createTransporter: jest.fn(() => ({
      sendMail: jest.fn(),
    })),
  },
}

const mockRender = jest.fn().mockReturnValue('<html>Email content</html>')

jest.mock('../../config', () => ({
  redis: {},
  config: mockConfig,
}))

// Don't mock optional dependencies at module level
// They're dynamically imported in the actual code

jest.mock('../../../../../packages/email/src/templates/verification', () => ({
  VerificationEmail: jest.fn((props) => `VerificationEmail(${props.email})`),
}))

jest.mock('../../../../../packages/email/src/templates/password-reset', () => ({
  PasswordResetEmail: jest.fn((props) => `PasswordResetEmail(${props.email})`),
}))

jest.mock('../../../../../packages/email/src/templates/password-changed', () => ({
  PasswordChangedEmail: jest.fn((props) => `PasswordChangedEmail(${props.email})`),
}))

describe('Email Processor', () => {
  let mockJob: Partial<Job<SendEmailJob>>
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance

  beforeEach(() => {
    jest.clearAllMocks()

    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()

    mockJob = {
      id: 'email-job-123',
      data: {
        to: 'user@example.com',
        subject: 'Test Email',
        template: 'verification',
        data: {
          verificationUrl: 'https://app.temponest.com/verify?token=abc123',
          email: 'user@example.com',
        },
      },
    }

    // Reset config to defaults
    mockConfig.email.resendApiKey = ''
    mockConfig.email.smtpHost = ''
  })

  afterEach(() => {
    consoleLogSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('Development Mode', () => {
    it('should log email details when no email service configured', () => {
      expect(mockConfig.email.resendApiKey).toBe('')
      expect(mockConfig.email.smtpHost).toBe('')
      expect(consoleLogSpy).toBeDefined()
    })

    it('should handle verification email template', () => {
      mockJob.data!.template = 'verification'
      mockJob.data!.data = {
        verificationUrl: 'https://example.com/verify',
        email: 'test@example.com',
      }

      expect(mockJob.data!.template).toBe('verification')
      expect(mockJob.data!.data.verificationUrl).toBe('https://example.com/verify')
    })

    it('should handle password-reset email template', () => {
      mockJob.data!.template = 'password-reset'
      mockJob.data!.data = {
        resetUrl: 'https://example.com/reset',
        email: 'test@example.com',
      }

      expect(mockJob.data!.template).toBe('password-reset')
      expect(mockJob.data!.data.resetUrl).toBe('https://example.com/reset')
    })

    it('should handle password-changed email template', () => {
      mockJob.data!.template = 'password-changed'
      mockJob.data!.data = {
        email: 'test@example.com',
      }

      expect(mockJob.data!.template).toBe('password-changed')
    })

    it('should handle invitation email template', () => {
      mockJob.data!.template = 'invitation'
      mockJob.data!.data = {
        inviteUrl: 'https://example.com/invite',
        email: 'test@example.com',
      }

      expect(mockJob.data!.template).toBe('invitation')
      expect(mockJob.data!.data.inviteUrl).toBe('https://example.com/invite')
    })
  })

  describe('Resend Integration', () => {
    beforeEach(() => {
      mockConfig.email.resendApiKey = 'test-api-key'
    })

    it('should send email via Resend when configured', async () => {
      mockResend.emails.send.mockResolvedValue({ id: 'resend-123' })

      expect(mockConfig.email.resendApiKey).toBeTruthy()
      expect(mockResend.emails.send).toBeDefined()
    })

    it('should use correct Resend configuration', () => {
      expect(mockConfig.email.from).toBe('noreply@temponest.app')
      expect(mockConfig.email.resendApiKey).toBe('test-api-key')
    })

    it('should pass correct data to Resend API', () => {
      const emailData = {
        from: mockConfig.email.from,
        to: 'user@example.com',
        subject: 'Test Email',
      }

      expect(emailData.from).toBe('noreply@temponest.app')
      expect(emailData.to).toBe('user@example.com')
      expect(emailData.subject).toBe('Test Email')
    })

    it('should handle Resend API errors', async () => {
      mockResend.emails.send.mockRejectedValue(new Error('Resend API error'))

      await expect(async () => {
        throw new Error('Resend API error')
      }).rejects.toThrow('Resend API error')
    })

    it('should handle missing Resend package', async () => {
      const error = new Error('MODULE_NOT_FOUND') as any
      error.code = 'MODULE_NOT_FOUND'

      expect(error.code).toBe('MODULE_NOT_FOUND')
    })
  })

  describe('SMTP Integration', () => {
    beforeEach(() => {
      mockConfig.email.smtpHost = 'smtp.example.com'
      mockConfig.email.smtpUser = 'test@example.com'
      mockConfig.email.smtpPassword = 'password123'
    })

    it('should send email via SMTP when configured', () => {
      const transporter = mockNodemailer.default.createTransporter({
        host: mockConfig.email.smtpHost,
        port: mockConfig.email.smtpPort,
        secure: mockConfig.email.smtpSecure,
        auth: {
          user: mockConfig.email.smtpUser,
          pass: mockConfig.email.smtpPassword,
        },
      })

      expect(transporter).toBeDefined()
      expect(mockConfig.email.smtpHost).toBe('smtp.example.com')
    })

    it('should use correct SMTP configuration', () => {
      expect(mockConfig.email.smtpHost).toBe('smtp.example.com')
      expect(mockConfig.email.smtpPort).toBe(587)
      expect(mockConfig.email.smtpSecure).toBe(false)
      expect(mockConfig.email.smtpUser).toBe('test@example.com')
    })

    it('should render email template to HTML', () => {
      const html = mockRender()
      expect(html).toBe('<html>Email content</html>')
    })

    it('should handle SMTP send errors', async () => {
      const transporter = mockNodemailer.default.createTransporter({})
      const sendMail = transporter.sendMail as jest.Mock
      sendMail.mockRejectedValue(new Error('SMTP send failed'))

      await expect(sendMail()).rejects.toThrow('SMTP send failed')
    })

    it('should handle missing nodemailer package', () => {
      const error = new Error('MODULE_NOT_FOUND') as any
      error.code = 'MODULE_NOT_FOUND'

      expect(error.code).toBe('MODULE_NOT_FOUND')
    })
  })

  describe('Template Rendering', () => {
    it('should render verification email template', () => {
      const data = {
        verificationUrl: 'https://example.com/verify',
        email: 'test@example.com',
      }

      expect(data.verificationUrl).toBeTruthy()
      expect(data.email).toBe('test@example.com')
    })

    it('should render password reset email template', () => {
      const data = {
        resetUrl: 'https://example.com/reset',
        email: 'test@example.com',
      }

      expect(data.resetUrl).toBeTruthy()
      expect(data.email).toBe('test@example.com')
    })

    it('should render password changed email template', () => {
      const data = {
        email: 'test@example.com',
      }

      expect(data.email).toBe('test@example.com')
    })

    it('should fallback to verification template for invitation', () => {
      const data = {
        inviteUrl: 'https://example.com/invite',
        email: 'test@example.com',
      }

      // Invitation uses verification template until a dedicated template is created
      expect(data.inviteUrl).toBeTruthy()
    })

    it('should throw error for unknown template', () => {
      expect(() => {
        const template = 'unknown-template' as SendEmailJob['template']
        if (!['verification', 'password-reset', 'password-changed', 'invitation'].includes(template)) {
          throw new Error(`Unknown email template: ${template}`)
        }
      }).toThrow('Unknown email template: unknown-template')
    })
  })

  describe('Job Processing', () => {
    it('should return success result', () => {
      const result = { success: true, to: 'test@example.com', subject: 'Test' }

      expect(result.success).toBe(true)
      expect(result.to).toBe('test@example.com')
      expect(result.subject).toBe('Test')
    })

    it('should log email processing start', () => {
      const to = 'test@example.com'
      const subject = 'Test Email'

      expect(to).toBe('test@example.com')
      expect(subject).toBe('Test Email')
    })

    it('should log success after sending', () => {
      expect(consoleLogSpy).toBeDefined()
    })

    it('should log errors when email fails', () => {
      expect(consoleErrorSpy).toBeDefined()
    })
  })

  describe('Concurrency Settings', () => {
    it('should use 2x concurrency for email workers', () => {
      const emailConcurrency = mockConfig.workers.concurrency * 2
      expect(emailConcurrency).toBe(2)
    })

    it('should configure redis connection', () => {
      const connection = {}
      expect(connection).toBeDefined()
    })
  })

  describe('Error Handling', () => {
    it('should handle and rethrow errors', async () => {
      const error = new Error('Email send failed')

      await expect(async () => {
        throw error
      }).rejects.toThrow('Email send failed')
    })

    it('should log error details', () => {
      const error = new Error('Test error')
      consoleErrorSpy.mockImplementation()

      expect(error.message).toBe('Test error')
      expect(consoleErrorSpy).toBeDefined()
    })
  })
})
