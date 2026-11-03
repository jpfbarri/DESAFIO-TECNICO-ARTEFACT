import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Empório da Música — Atendimento Virtual Oficial (Campo Grande/MS)",
  description:
    "Assistente oficial da Empório da Música. Consulte catálogo de instrumentos musicais, preços com 5% de desconto no PIX, rastreamento de pedidos e políticas da loja em Campo Grande/MS.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-screen w-screen overflow-hidden bg-[#FAF8F5] font-sans text-[#1C1917] antialiased selection:bg-[#FEF3C7] selection:text-[#92400E]">
        {children}
      </body>
    </html>
  );
}
