import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  devIndicators: false,
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/artifacts/**",
      },
    ],
    dangerouslyAllowLocalIP: true,
  },
};

export default nextConfig;
