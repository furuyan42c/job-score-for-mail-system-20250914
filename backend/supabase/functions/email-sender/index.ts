/**
 * T072: Email Sender Edge Function
 *
 * Handles email sending operations including:
 * - Transactional emails
 * - Notification emails
 * - Bulk email campaigns
 * - Email templates
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders, handleCors, createResponse } from '../_shared/cors.ts'
import { createAdminClient } from '../_shared/supabase.ts'
import { Logger } from '../_shared/logger.ts'

const logger = new Logger('email-sender')

interface EmailRequest {
  email_type: 'transactional' | 'notification' | 'bulk' | 'template'
  to: string | string[]
  from?: string
  subject: string
  template_id?: string
  template_data?: any
  content?: {
    html?: string
    text?: string
  }
  attachments?: Array<{
    filename: string
    content: string // base64 encoded
    content_type: string
  }>
  priority?: 'high' | 'normal' | 'low'
  send_at?: string // ISO date for scheduled sending
  metadata?: any
}

interface EmailResult {
  success: boolean
  message_id?: string
  recipient_count?: number
  error?: string
  delivery_status?: string
}

serve(async (req) => {
  // Handle CORS
  const corsResponse = handleCors(req)
  if (corsResponse) return corsResponse

  try {
    logger.info('Email sender started', { method: req.method })

    if (req.method !== 'POST') {
      return createResponse({ error: 'Method not allowed' }, 405)
    }

    // Parse request body
    const emailRequest: EmailRequest = await req.json()
    logger.info('Received email request', {
      email_type: emailRequest.email_type,
      recipient_count: Array.isArray(emailRequest.to) ? emailRequest.to.length : 1
    })

    // Validate email request
    const validation = validateEmailRequest(emailRequest)
    if (!validation.valid) {
      return createResponse({ error: validation.error }, 400)
    }

    // Create Supabase admin client
    const supabase = createAdminClient()

    let result: EmailResult

    try {
      // Process email based on type
      switch (emailRequest.email_type) {
        case 'transactional':
          result = await sendTransactionalEmail(supabase, emailRequest)
          break
        case 'notification':
          result = await sendNotificationEmail(supabase, emailRequest)
          break
        case 'bulk':
          result = await sendBulkEmail(supabase, emailRequest)
          break
        case 'template':
          result = await sendTemplateEmail(supabase, emailRequest)
          break
        default:
          throw new Error(`Unknown email type: ${emailRequest.email_type}`)
      }

      // Log email sending activity
      await logEmailActivity(supabase, emailRequest, result)

      logger.info('Email sent successfully', {
        email_type: emailRequest.email_type,
        message_id: result.message_id,
        recipient_count: result.recipient_count
      })

    } catch (error) {
      const errorMessage = error.message || 'Unknown error'
      logger.error('Email sending failed', { error: errorMessage })

      result = {
        success: false,
        error: errorMessage
      }

      // Log failed email attempt
      await logEmailActivity(supabase, emailRequest, result)
    }

    return createResponse(result)

  } catch (error) {
    logger.error('Unhandled error in email sender', { error: error.message })
    return createResponse({ error: 'Internal server error' }, 500)
  }
})

function validateEmailRequest(request: EmailRequest): { valid: boolean; error?: string } {
  if (!request.email_type) {
    return { valid: false, error: 'Missing email_type' }
  }

  if (!request.to) {
    return { valid: false, error: 'Missing recipient (to)' }
  }

  if (!request.subject) {
    return { valid: false, error: 'Missing email subject' }
  }

  if (request.email_type === 'template' && !request.template_id) {
    return { valid: false, error: 'Missing template_id for template email' }
  }

  if (request.email_type !== 'template' && !request.content?.html && !request.content?.text) {
    return { valid: false, error: 'Missing email content (html or text)' }
  }

  // Validate email addresses
  const recipients = Array.isArray(request.to) ? request.to : [request.to]
  for (const email of recipients) {
    if (!isValidEmail(email)) {
      return { valid: false, error: `Invalid email address: ${email}` }
    }
  }

  return { valid: true }
}

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

async function sendTransactionalEmail(supabase: any, request: EmailRequest): Promise<EmailResult> {
  logger.info('Sending transactional email')

  try {
    // Get email service configuration
    const emailConfig = await getEmailServiceConfig(supabase)

    // Prepare email data
    const emailData = {
      to: request.to,
      from: request.from || emailConfig.default_from,
      subject: request.subject,
      html: request.content?.html,
      text: request.content?.text,
      attachments: request.attachments,
      headers: {
        'X-Email-Type': 'transactional',
        'X-Priority': request.priority || 'normal'
      }
    }

    // Send email using configured service
    const messageId = await sendEmailViaService(emailConfig, emailData)

    return {
      success: true,
      message_id: messageId,
      recipient_count: Array.isArray(request.to) ? request.to.length : 1,
      delivery_status: 'sent'
    }

  } catch (error) {
    throw new Error(`Transactional email failed: ${error.message}`)
  }
}

async function sendNotificationEmail(supabase: any, request: EmailRequest): Promise<EmailResult> {
  logger.info('Sending notification email')

  try {
    // Get notification email template if not provided
    let emailContent = request.content

    if (!emailContent) {
      emailContent = await getNotificationTemplate(supabase, request.metadata?.notification_type)
    }

    // Apply any template data
    if (request.template_data) {
      emailContent = await applyTemplateData(emailContent, request.template_data)
    }

    const emailConfig = await getEmailServiceConfig(supabase)

    const emailData = {
      to: request.to,
      from: request.from || emailConfig.notification_from,
      subject: request.subject,
      html: emailContent.html,
      text: emailContent.text,
      headers: {
        'X-Email-Type': 'notification',
        'X-Priority': request.priority || 'normal'
      }
    }

    const messageId = await sendEmailViaService(emailConfig, emailData)

    return {
      success: true,
      message_id: messageId,
      recipient_count: Array.isArray(request.to) ? request.to.length : 1,
      delivery_status: 'sent'
    }

  } catch (error) {
    throw new Error(`Notification email failed: ${error.message}`)
  }
}

async function sendBulkEmail(supabase: any, request: EmailRequest): Promise<EmailResult> {
  logger.info('Sending bulk email')

  try {
    if (!Array.isArray(request.to)) {
      throw new Error('Bulk email requires array of recipients')
    }

    // Check bulk email limits
    const bulkLimits = await getBulkEmailLimits(supabase)
    if (request.to.length > bulkLimits.max_recipients) {
      throw new Error(`Recipient count exceeds limit: ${request.to.length} > ${bulkLimits.max_recipients}`)
    }

    const emailConfig = await getEmailServiceConfig(supabase)

    // Split recipients into batches
    const batchSize = bulkLimits.batch_size || 100
    const batches = []

    for (let i = 0; i < request.to.length; i += batchSize) {
      batches.push(request.to.slice(i, i + batchSize))
    }

    let totalSent = 0
    const messageIds = []

    // Send emails in batches
    for (const batch of batches) {
      const emailData = {
        to: batch,
        from: request.from || emailConfig.bulk_from,
        subject: request.subject,
        html: request.content?.html,
        text: request.content?.text,
        headers: {
          'X-Email-Type': 'bulk',
          'X-Priority': request.priority || 'low'
        }
      }

      const messageId = await sendEmailViaService(emailConfig, emailData)
      messageIds.push(messageId)
      totalSent += batch.length

      // Add delay between batches to respect rate limits
      if (batches.length > 1) {
        await new Promise(resolve => setTimeout(resolve, bulkLimits.batch_delay || 1000))
      }
    }

    return {
      success: true,
      message_id: messageIds.join(','),
      recipient_count: totalSent,
      delivery_status: 'sent'
    }

  } catch (error) {
    throw new Error(`Bulk email failed: ${error.message}`)
  }
}

async function sendTemplateEmail(supabase: any, request: EmailRequest): Promise<EmailResult> {
  logger.info('Sending template email', { template_id: request.template_id })

  try {
    // Get email template
    const template = await getEmailTemplate(supabase, request.template_id!)
    if (!template) {
      throw new Error(`Template not found: ${request.template_id}`)
    }

    // Apply template data
    const emailContent = await applyTemplateData(template.content, request.template_data || {})

    const emailConfig = await getEmailServiceConfig(supabase)

    const emailData = {
      to: request.to,
      from: request.from || template.default_from || emailConfig.default_from,
      subject: await applyTemplateData({ text: request.subject || template.subject }, request.template_data || {}),
      html: emailContent.html,
      text: emailContent.text,
      headers: {
        'X-Email-Type': 'template',
        'X-Template-ID': request.template_id,
        'X-Priority': request.priority || 'normal'
      }
    }

    const messageId = await sendEmailViaService(emailConfig, emailData)

    return {
      success: true,
      message_id: messageId,
      recipient_count: Array.isArray(request.to) ? request.to.length : 1,
      delivery_status: 'sent'
    }

  } catch (error) {
    throw new Error(`Template email failed: ${error.message}`)
  }
}

async function getEmailServiceConfig(supabase: any): Promise<any> {
  // Get email service configuration from database
  const { data, error } = await supabase
    .from('email_config')
    .select('*')
    .eq('active', true)
    .single()

  if (error) {
    logger.warn('Using default email config', { error: error.message })
    return {
      service: 'smtp',
      default_from: 'noreply@example.com',
      notification_from: 'notifications@example.com',
      bulk_from: 'bulk@example.com'
    }
  }

  return data.config
}

async function getEmailTemplate(supabase: any, templateId: string): Promise<any> {
  const { data, error } = await supabase
    .from('email_templates')
    .select('*')
    .eq('id', templateId)
    .eq('active', true)
    .single()

  if (error) {
    throw new Error(`Failed to fetch template: ${error.message}`)
  }

  return data
}

async function getNotificationTemplate(supabase: any, notificationType: string): Promise<any> {
  const { data, error } = await supabase
    .from('email_templates')
    .select('*')
    .eq('type', 'notification')
    .eq('notification_type', notificationType)
    .eq('active', true)
    .single()

  if (error) {
    // Return default notification template
    return {
      html: '<p>{{message}}</p>',
      text: '{{message}}'
    }
  }

  return data.content
}

async function getBulkEmailLimits(supabase: any): Promise<any> {
  const { data, error } = await supabase
    .from('system_config')
    .select('value')
    .eq('key', 'bulk_email_limits')
    .single()

  if (error) {
    return {
      max_recipients: 1000,
      batch_size: 100,
      batch_delay: 1000
    }
  }

  return JSON.parse(data.value)
}

async function applyTemplateData(content: any, data: any): Promise<any> {
  // Simple template variable replacement
  let html = content.html || ''
  let text = content.text || ''

  for (const [key, value] of Object.entries(data)) {
    const placeholder = `{{${key}}}`
    html = html.replace(new RegExp(placeholder, 'g'), String(value))
    text = text.replace(new RegExp(placeholder, 'g'), String(value))
  }

  return { html, text }
}

async function sendEmailViaService(config: any, emailData: any): Promise<string> {
  // Placeholder for actual email service integration
  // In a real implementation, this would integrate with:
  // - SendGrid
  // - AWS SES
  // - Mailgun
  // - SMTP server
  // etc.

  logger.info('Simulating email send', {
    service: config.service,
    recipients: Array.isArray(emailData.to) ? emailData.to.length : 1
  })

  // Simulate email sending delay
  await new Promise(resolve => setTimeout(resolve, 100))

  // Generate mock message ID
  const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  return messageId
}

async function logEmailActivity(supabase: any, request: EmailRequest, result: EmailResult) {
  try {
    const { error } = await supabase
      .from('email_logs')
      .insert({
        email_type: request.email_type,
        recipients: Array.isArray(request.to) ? request.to : [request.to],
        subject: request.subject,
        message_id: result.message_id,
        success: result.success,
        error: result.error,
        metadata: {
          priority: request.priority,
          template_id: request.template_id,
          delivery_status: result.delivery_status
        },
        sent_at: new Date().toISOString()
      })

    if (error) {
      logger.error('Failed to log email activity', { error: error.message })
    }
  } catch (error) {
    logger.error('Error logging email activity', { error: error.message })
  }
}