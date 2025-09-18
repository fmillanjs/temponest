'use client';

import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (session) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Bienvenido a TempoNest, {session.user.name}
            </h1>
            <p className="text-xl text-gray-600">
              Tu plataforma completa para gestionar tu tienda
            </p>
          </div>

          <div className="text-center">
            <Link href="/dashboard">
              <Button size="lg" className="bg-green-600 hover:bg-green-700">
                Ir al Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            TempoNest
          </h1>
          <p className="text-2xl text-gray-600 mb-4">
            SaaS completo para pequeñas tiendas en México
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Gestiona tu inventario, ventas, clientes y finanzas con integración WhatsApp
            y cumplimiento fiscal SAT
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          <Card>
            <CardHeader>
              <CardTitle>🏪 Punto de Venta</CardTitle>
              <CardDescription>
                Sistema de ventas rápido con códigos de barras y WhatsApp
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Ventas con código de barras</li>
                <li>• Múltiples métodos de pago</li>
                <li>• Recibos por WhatsApp</li>
                <li>• Modo offline</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>📦 Inventario</CardTitle>
              <CardDescription>
                Control completo de stock con alertas inteligentes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Alertas de stock bajo</li>
                <li>• Control de lotes y caducidad</li>
                <li>• Multi-ubicación</li>
                <li>• Reportes automáticos</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>📊 Finanzas</CardTitle>
              <CardDescription>
                Análisis financiero y cumplimiento SAT/CFDI
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Facturación CFDI 4.0</li>
                <li>• Análisis de rentabilidad</li>
                <li>• Flujo de caja</li>
                <li>• Reportes fiscales</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="text-center space-x-4">
          <Link href="/auth/signin">
            <Button size="lg" className="bg-green-600 hover:bg-green-700">
              Iniciar Sesión
            </Button>
          </Link>
          <Link href="/auth/register">
            <Button size="lg" variant="outline">
              Crear Cuenta
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
