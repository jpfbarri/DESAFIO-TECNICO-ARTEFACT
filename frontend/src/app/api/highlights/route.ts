import { NextResponse } from "next/server";

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL || "http://127.0.0.1:8000";

const FALLBACK_PROMOTIONS = [
  {
    product_id: 121,
    name: "Ohana CK-20 Concert Natural",
    price_brl: 1199.0,
    discount_percent: 20.0,
    campaign: "Desconto Exclusivo",
  },
  {
    product_id: 90,
    name: "Crafter HT-100 Folk Aço Natural",
    price_brl: 2399.0,
    discount_percent: 18.0,
    campaign: "Desconto Exclusivo",
  },
  {
    product_id: 127,
    name: "Kalani KAL-700T Tenor Natural",
    price_brl: 899.0,
    discount_percent: 10.0,
    campaign: "Oferta Especial",
  },
  {
    product_id: 94,
    name: "Taylor 110e Dreadnought Natural",
    price_brl: 5999.0,
    discount_percent: 8.0,
    campaign: "Desconto Exclusivo",
  },
];

export async function GET() {
  try {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/catalog/highlights`, {
      cache: "no-store",
    });
    if (!resp.ok) {
      return NextResponse.json({
        active_promotions: FALLBACK_PROMOTIONS,
        backend_online: false,
      });
    }
    const json = await resp.json();
    return NextResponse.json({
      active_promotions: json.active_promotions || FALLBACK_PROMOTIONS,
      backend_online: true,
    });
  } catch {
    return NextResponse.json({
      active_promotions: FALLBACK_PROMOTIONS,
      backend_online: false,
    });
  }
}

