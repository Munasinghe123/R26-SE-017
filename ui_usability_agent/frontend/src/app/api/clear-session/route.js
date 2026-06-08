import { NextResponse } from 'next/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST() {
  try {
    const res = await fetch('http://localhost:8000/api/clear-session', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) return NextResponse.json({ error: data.detail || 'Failed.' }, { status: res.status });
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json({ error: e.message || 'Clear failed.' }, { status: 500 });
  }
}