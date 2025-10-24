import { Worker, Job } from 'bullmq'
import { redis, config } from '../config'
import type { SendEmailJob } from '@temponest/types'

// Import email templates
import { VerificationEmail } from '@temponest/email/templates/verification'
import { PasswordResetEmail } from '@temponest/email/templates/password-reset'
import { PasswordChangedEmail } from '@temponest/email/templates/password-changed'

/**
 * Process email job
 * EXPORTED FOR TESTING - Contains all business logic
 */
export async function processEmail(job: Job<SendEmailJob>): Promise<{ success: true; to: string; subject: string }> {
  const { to, subject, template, data } = job.data

  console.log(`📧 Sending email to ${to}: ${subject}`)

  try {
    if (config.email.resendApiKey) {
      // Production: Send via Resend
      await sendViaResend(to, subject, template, data)
      console.log(`  ✅ Email sent via Resend`)
    } else if (config.email.smtpHost) {
      // Alternative: Send via SMTP
      await sendViaSmtp(to, subject, template, data)
      console.log(`  ✅ Email sent via SMTP`)
    } else {
      // Development mode - log to console
      console.log(`  📮 [DEV] Email would be sent to: ${to}`)
      console.log(`  📋 Template: ${template}`)
      console.log(`  📊 Data:`, data)
      console.log(`  📝 Subject: ${subject}`)
    }

    return { success: true, to, subject }
  } catch (error) {
    console.error(`❌ Email send failed:`, error)
    throw error
  }
}

/**
 * Email processor worker
 * Sends emails using Resend or SMTP
 */
export const emailWorker = new Worker<SendEmailJob>(
  'emails',
  processEmail,
  {
    connection: redis,
    concurrency: config.workers.concurrency * 2, // Higher concurrency for emails
  }
)

/**
 * Send email via Resend
 */
async function sendViaResend(
  to: string,
  subject: string,
  template: SendEmailJob['template'],
  data: Record<string, unknown>
) {
  try {
    // Dynamically import Resend to avoid errors if not installed
    const { Resend } = await import('resend')
    const resend = new Resend(config.email.resendApiKey)

    const emailTemplate = getEmailTemplate(template, data)

    await resend.emails.send({
      from: config.email.from,
      to,
      subject,
      react: emailTemplate,
    })
  } catch (error) {
    if ((error as any).code === 'MODULE_NOT_FOUND') {
      throw new Error(
        'Resend package not installed. Run: pnpm add resend -w'
      )
    }
    throw error
  }
}

/**
 * Send email via SMTP
 */
async function sendViaSmtp(
  to: string,
  subject: string,
  template: SendEmailJob['template'],
  data: Record<string, unknown>
) {
  try {
    // Dynamically import nodemailer
    const nodemailer = await import('nodemailer')
    const { render } = await import('@react-email/render')

    const transporter = nodemailer.default.createTransporter({
      host: config.email.smtpHost,
      port: config.email.smtpPort || 587,
      secure: config.email.smtpSecure || false,
      auth: {
        user: config.email.smtpUser,
        pass: config.email.smtpPassword,
      },
    })

    const emailTemplate = getEmailTemplate(template, data)
    const html = render(emailTemplate)

    await transporter.sendMail({
      from: config.email.from,
      to,
      subject,
      html,
    })
  } catch (error) {
    if ((error as any).code === 'MODULE_NOT_FOUND') {
      throw new Error(
        'Nodemailer package not installed. Run: pnpm add nodemailer @types/nodemailer -w'
      )
    }
    throw error
  }
}

/**
 * Get email template component based on template name
 */
function getEmailTemplate(template: SendEmailJob['template'], data: Record<string, unknown>) {
  switch (template) {
    case 'verification':
      return VerificationEmail({
        verificationUrl: data.verificationUrl as string,
        email: data.email as string,
      })

    case 'password-reset':
      return PasswordResetEmail({
        resetUrl: data.resetUrl as string,
        email: data.email as string,
      })

    case 'password-changed':
      return PasswordChangedEmail({
        email: data.email as string,
      })

    case 'invitation':
      // TODO: Create invitation email template
      return VerificationEmail({
        verificationUrl: data.inviteUrl as string,
        email: data.email as string,
      })

    default:
      throw new Error(`Unknown email template: ${template}`)
  }
}

emailWorker.on('completed', (job) => {
  console.log(`✅ Email sent: ${job.id}`)
})

emailWorker.on('failed', (job, err) => {
  console.error(`❌ Email job ${job?.id} failed:`, err.message)
})
