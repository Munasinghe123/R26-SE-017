import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const screenId = searchParams.get('screenId');
    const url = new URL('http://localhost:8000/api/outputs');
    if (screenId) url.searchParams.set('screenId', screenId);
    const res = await fetch(url.toString());
    const data = await res.json();
    if (!res.ok) return NextResponse.json({ error: data.detail || 'Failed.' }, { status: res.status });
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Failed.' }, { status: 500 });
  }
}