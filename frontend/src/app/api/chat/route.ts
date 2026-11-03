import { NextRequest, NextResponse } from "next/server";

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message =
      body.message ||
      (Array.isArray(body.messages) && body.messages.length > 0
        ? body.messages[body.messages.length - 1]?.content
        : "");
    const threadId = body.thread_id || body.id || "default-session";

    const upstream = await fetch(`${FASTAPI_BASE_URL}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, thread_id: threadId }),
    });

    if (!upstream.ok || !upstream.body) {
      const errorText = await upstream.text();
      return NextResponse.json(
        { error: `Erro no backend FastAPI: ${errorText}` },
        { status: upstream.status || 502 }
      );
    }

    return new Response(upstream.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (err) {
    const msg =
      err instanceof Error
        ? err.message
        : "Falha ao conectar ao servidor FastAPI em 127.0.0.1:8000";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const threadId = searchParams.get("thread_id") || "default-session";
    const upstream = await fetch(
      `${FASTAPI_BASE_URL}/api/threads/${encodeURIComponent(threadId)}`,
      { method: "DELETE" }
    );
    const result = await upstream.json();
    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ status: "offline" }, { status: 200 });
  }
}

