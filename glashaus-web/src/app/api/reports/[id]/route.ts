import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> } // Params are promises in Next.js 15
) {
  const { id } = await params;
  const apiUrl = process.env.API_INTERNAL_URL || 'http://localhost:8000';

  try {
    const res = await fetch(`${apiUrl}/reports/${id}`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Report Not Found" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Upstream Unreachable" }, { status: 503 });
  }
}
