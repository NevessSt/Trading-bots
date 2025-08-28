const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

/**
 * Metro configuration
 * https://facebook.github.io/metro/docs/configuration
 */
const config = {
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
  resolver: {
    alias: {
      // Add path aliases for cleaner imports
      '@': './src',
      '@components': './src/components',
      '@screens': './src/screens',
      '@context': './src/context',
      '@services': './src/services',
      '@utils': './src/utils',
      '@types': './src/types',
    },
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);