/** @type {import('next').NextConfig} */
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const nextConfig = {
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:5328/api/:path*'
            : '/api/',
      },
    ];
  },
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      // Modify the config for production and client-side builds
      config.module.rules.push({
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader'],
      });

      config.plugins.push(
        new MiniCssExtractPlugin({
          filename: '[name].css',
          chunkFilename: '[id].css',
        })
      );
    }

    return config;
  },
};

module.exports = nextConfig;
