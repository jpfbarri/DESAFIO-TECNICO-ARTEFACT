import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          DEFAULT: "#FAF8F5",
          sidebar: "#F3EFE6",
          border: "#E7E2D8",
        },
        amber: {
          accent: "#D97706",
          hover: "#B45309",
          soft: "#FEF3C7",
          text: "#92400E",
        },
        ink: {
          DEFAULT: "#1C1917",
          muted: "#57534E",
          cents: "#A8A29E",
        },
      },
      borderRadius: {
        card: "20px",
      },
      fontFamily: {
        sans: ["Poppins", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        poppins: ["Poppins", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
