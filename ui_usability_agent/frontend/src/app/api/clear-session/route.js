import { NextResponse } from 'next/server';
import fs from 'node:fs/promises';
import path from 'node:path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const FRONTEND_DIR = process.cwd();
const AGENT_ROOT = path.resolve(FRONTEND_DIR, '..');

export async function POST() {
  try {
    const toDelete = [
      path.join(AGENT_ROOT, 'outputs', 'screen_plan.json'),
      path.join(AGENT_ROOT, 'outputs', 'generated_screens'),
      path.join(AGENT_ROOT, 'outputs', 'score_reports'),
      path.join(AGENT_ROOT, 'samples', 'sample_requirements.json'),
    ];

    for (const p of toDelete) {
      try {
        const stat = await fs.stat(p);
        if (stat.isDirectory()) {
          await fs.rm(p, { recursive: true, force: true });
        } else {
          await fs.unlink(p);
        }
      } catch {
        // file didn't exist — fine
      }
    }

    return NextResponse.json({ cleared: true });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Clear failed.' },
      { status: 500 }
    );
  }
}