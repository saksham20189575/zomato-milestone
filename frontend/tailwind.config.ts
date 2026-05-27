import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#14141c",
          elevated: "#1a1a22",
          card: "#14141c",
          input: "#121218",
        },
        border: {
          DEFAULT: "#252530",
          muted: "#2a2a35",
        },
        accent: {
          DEFAULT: "#22d3ee",
          muted: "rgba(34, 211, 238, 0.12)",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "page-gradient":
          "radial-gradient(ellipse 120% 80% at 50% -20%, #1a1a24 0%, #0a0a0f 45%, #060608 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
