import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const res = await fetch('http://localhost:8000/api/reports');
    const data = await res.json();
    if (!res.ok) return NextResponse.json({ error: data.detail || 'Failed.' }, { status: res.status });
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Failed.' }, { status: 500 });
  }
}