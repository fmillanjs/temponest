import {
  Body,
  Button,
  Container,
  Head,
  Heading,
  Html,
  Preview,
  Section,
  Text,
} from '@react-email/components'
import * as React from 'react'

interface WelcomeEmailProps {
  name: string
  loginUrl?: string
}

export function WelcomeEmail({ name, loginUrl }: WelcomeEmailProps) {
  return (
    <Html>
      <Head />
      <Preview>Welcome to TempoNest! Start building your SaaS projects today.</Preview>
      <Body style={main}>
        <Container style={container}>
          <Heading style={h1}>Welcome to TempoNest!</Heading>
          <Text style={text}>Hi {name},</Text>
          <Text style={text}>
            We're excited to have you on board. TempoNest makes it easy to generate and deploy
            SaaS applications in minutes.
          </Text>
          <Section style={buttonContainer}>
            <Button style={button} href={loginUrl || 'https://temponest.com/login'}>
              Get Started
            </Button>
          </Section>
          <Text style={text}>
            If you have any questions, feel free to reply to this email. We're here to help!
          </Text>
          <Text style={footer}>
            TempoNest Team
            <br />
            Building the future of SaaS development
          </Text>
        </Container>
      </Body>
    </Html>
  )
}

const main = {
  backgroundColor: '#f6f9fc',
  fontFamily:
    '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Ubuntu,sans-serif',
}

const container = {
  backgroundColor: '#ffffff',
  margin: '0 auto',
  padding: '20px 0 48px',
  marginBottom: '64px',
}

const h1 = {
  color: '#333',
  fontSize: '24px',
  fontWeight: 'bold',
  margin: '40px 0',
  padding: '0',
  textAlign: 'center' as const,
}

const text = {
  color: '#333',
  fontSize: '16px',
  lineHeight: '26px',
  margin: '16px 0',
}

const buttonContainer = {
  textAlign: 'center' as const,
  margin: '32px 0',
}

const button = {
  backgroundColor: '#000',
  borderRadius: '5px',
  color: '#fff',
  fontSize: '16px',
  fontWeight: 'bold',
  textDecoration: 'none',
  textAlign: 'center' as const,
  display: 'inline-block',
  padding: '12px 30px',
}

const footer = {
  color: '#8898aa',
  fontSize: '12px',
  lineHeight: '16px',
  margin: '32px 0 0 0',
  textAlign: 'center' as const,
}

export default WelcomeEmail
