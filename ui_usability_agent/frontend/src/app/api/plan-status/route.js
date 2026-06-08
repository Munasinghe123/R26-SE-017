import { NextResponse } from 'next/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const res = await fetch('http://localhost:8000/api/plan-status');
    const data = await res.json();
    if (!res.ok) return NextResponse.json({ screens: [] });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ screens: [] });
  }
}
