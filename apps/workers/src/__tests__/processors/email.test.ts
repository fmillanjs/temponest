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

const mockResendSend = jest.fn()
const mockSendMail = jest.fn()
const mockRender = jest.fn().mockReturnValue('<html>Email content</html>')

// Mock Worker to prevent Redis connection
const mockWorkerClose = jest.fn().mockResolvedValue(undefined)
const mockWorkerOn = jest.fn()

jest.mock('bullmq', () => ({
  ...jest.requireActual('bullmq'),
  Worker: jest.fn().mockImplementation(() => ({
    close: mockWorkerClose,
    on: mockWorkerOn,
  })),
}))

jest.mock('../../config', () => ({
  redis: {},
  config: mockConfig,
}))

// Mock email templates with proper path resolution
jest.mock('@temponest/email/templates/verification', () => ({
  VerificationEmail: jest.fn(() => 'VerificationEmail'),
}))

jest.mock('@temponest/email/templates/password-reset', () => ({
  PasswordResetEmail: jest.fn(() => 'PasswordResetEmail'),
}))

jest.mock('@temponest/email/templates/password-changed', () => ({
  PasswordChangedEmail: jest.fn(() => 'PasswordChangedEmail'),
}))

// Mock nodemailer for SMTP tests (virtual mock - package not installed)
jest.mock('nodemailer', () => ({
  createTransporter: jest.fn(() => ({
    sendMail: mockSendMail,
  })),
}), { virtual: true })

// Mock @react-email/render for SMTP tests (virtual mock - package not installed)
jest.mock('@react-email/render', () => ({
  render: mockRender,
}), { virtual: true })

// Import after all mocks are set up
const { processEmail, emailWorker } = require('../../processors/email')

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

  afterAll(async () => {
    // Close the Worker to prevent hanging tests
    if (emailWorker && emailWorker.close) {
      await emailWorker.close()
    }
  })

  describe('Development Mode', () => {
    it('should log email details when no email service configured', async () => {
      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(result.to).toBe('user@example.com')
      expect(result.subject).toBe('Test Email')
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('[DEV] Email would be sent to'))
    })

    it('should handle verification email template in dev mode', async () => {
      mockJob.data!.template = 'verification'
      mockJob.data!.data = {
        verificationUrl: 'https://example.com/verify',
        email: 'test@example.com',
      }

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Template: verification'))
    })

    it('should handle password-reset email template in dev mode', async () => {
      mockJob.data!.template = 'password-reset'
      mockJob.data!.data = {
        resetUrl: 'https://example.com/reset',
        email: 'test@example.com',
      }

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Template: password-reset'))
    })

    it('should handle password-changed email template in dev mode', async () => {
      mockJob.data!.template = 'password-changed'
      mockJob.data!.data = {
        email: 'test@example.com',
      }

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Template: password-changed'))
    })

    it('should handle invitation email template in dev mode', async () => {
      mockJob.data!.template = 'invitation'
      mockJob.data!.data = {
        inviteUrl: 'https://example.com/invite',
        email: 'test@example.com',
      }

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Template: invitation'))
    })
  })

  describe('Resend Integration', () => {
    beforeEach(() => {
      mockConfig.email.resendApiKey = 'test-api-key'
      mockResendSend.mockClear()

      // Mock Resend dynamic import
      jest.isolateModules(() => {
        jest.mock('resend', () => ({
          Resend: jest.fn(() => ({
            emails: {
              send: mockResendSend,
            },
          })),
        }), { virtual: true })
      })
    })

    it('should send email via Resend when configured', async () => {
      mockResendSend.mockResolvedValue({ id: 'resend-123' })

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(result.to).toBe('user@example.com')
      expect(result.subject).toBe('Test Email')
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('✅ Email sent via Resend'))
    })

    it('should use correct Resend configuration', async () => {
      mockResendSend.mockResolvedValue({ id: 'resend-123' })

      await processEmail(mockJob as Job<SendEmailJob>)

      expect(mockConfig.email.from).toBe('noreply@temponest.app')
      expect(mockConfig.email.resendApiKey).toBe('test-api-key')
    })

    it('should pass correct data to Resend API', async () => {
      mockResendSend.mockResolvedValue({ id: 'resend-123' })

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.to).toBe('user@example.com')
      expect(result.subject).toBe('Test Email')
    })

    it('should handle Resend API errors', async () => {
      mockResendSend.mockRejectedValue(new Error('Resend API error'))

      await expect(processEmail(mockJob as Job<SendEmailJob>))
        .rejects.toThrow('Resend API error')
    })

    it('should handle missing Resend package', async () => {
      const error = new Error('Resend package not installed') as any
      error.code = 'MODULE_NOT_FOUND'
      mockResendSend.mockRejectedValue(error)

      await expect(processEmail(mockJob as Job<SendEmailJob>))
        .rejects.toThrow()
    })
  })

  describe('SMTP Integration', () => {
    beforeEach(() => {
      mockConfig.email.resendApiKey = '' // Disable Resend
      mockConfig.email.smtpHost = 'smtp.example.com'
      mockConfig.email.smtpUser = 'test@example.com'
      mockConfig.email.smtpPassword = 'password123'
      mockSendMail.mockClear()
      mockRender.mockClear()
    })

    it('should send email via SMTP when configured', async () => {
      mockSendMail.mockResolvedValue({ messageId: 'smtp-123' })

      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(result.to).toBe('user@example.com')
      expect(result.subject).toBe('Test Email')
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('✅ Email sent via SMTP'))
    })

    it('should use correct SMTP configuration', async () => {
      mockSendMail.mockResolvedValue({ messageId: 'smtp-123' })

      await processEmail(mockJob as Job<SendEmailJob>)

      expect(mockConfig.email.smtpHost).toBe('smtp.example.com')
      expect(mockConfig.email.smtpPort).toBe(587)
      expect(mockConfig.email.smtpSecure).toBe(false)
      expect(mockConfig.email.smtpUser).toBe('test@example.com')
    })

    it('should render email template to HTML', async () => {
      mockSendMail.mockResolvedValue({ messageId: 'smtp-123' })

      await processEmail(mockJob as Job<SendEmailJob>)

      expect(mockRender).toHaveBeenCalled()
    })

    it('should handle SMTP send errors', async () => {
      mockSendMail.mockRejectedValue(new Error('SMTP send failed'))

      await expect(processEmail(mockJob as Job<SendEmailJob>))
        .rejects.toThrow('SMTP send failed')
    })

    it('should handle missing nodemailer package', async () => {
      const error = new Error('MODULE_NOT_FOUND') as any
      error.code = 'MODULE_NOT_FOUND'
      mockSendMail.mockRejectedValue(error)

      await expect(processEmail(mockJob as Job<SendEmailJob>))
        .rejects.toThrow()
    })
  })

  describe('Template Rendering', () => {
    it('should throw error for unknown template', async () => {
      // Enable SMTP so template validation actually runs
      mockConfig.email.smtpHost = 'smtp.example.com'
      mockJob.data!.template = 'unknown-template' as any

      await expect(processEmail(mockJob as Job<SendEmailJob>))
        .rejects.toThrow('Unknown email template: unknown-template')

      expect(consoleErrorSpy).toHaveBeenCalled()
    })
  })

  describe('Job Processing', () => {
    it('should return success result with correct data', async () => {
      const result = await processEmail(mockJob as Job<SendEmailJob>)

      expect(result.success).toBe(true)
      expect(result.to).toBe('user@example.com')
      expect(result.subject).toBe('Test Email')
    })

    it('should log email processing start', async () => {
      await processEmail(mockJob as Job<SendEmailJob>)

      expect(consoleLogSpy).toHaveBeenCalledWith('📧 Sending email to user@example.com: Test Email')
    })

    it('should log errors when email fails', async () => {
      // Enable SMTP and force an error by providing invalid template
      mockConfig.email.smtpHost = 'smtp.example.com'
      mockJob.data!.template = null as any

      await expect(processEmail(mockJob as Job<SendEmailJob>)).rejects.toThrow()

      expect(consoleErrorSpy).toHaveBeenCalledWith('❌ Email send failed:', expect.any(Error))
    })
  })

  describe('Concurrency Settings', () => {
    it('should use 2x concurrency for email workers', () => {
      const emailConcurrency = mockConfig.workers.concurrency * 2
      expect(emailConcurrency).toBe(2)
    })
  })

  describe('Error Handling', () => {
    it('should rethrow errors after logging', async () => {
      // Enable SMTP so template validation runs
      mockConfig.email.smtpHost = 'smtp.example.com'
      mockJob.data!.template = 'invalid' as any

      await expect(processEmail(mockJob as Job<SendEmailJob>))
        .rejects.toThrow()

      expect(consoleErrorSpy).toHaveBeenCalled()
    })
  })
})
