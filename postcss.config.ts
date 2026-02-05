import tailwindcss from '@tailwindcss/postcss';
import autoprefixer from 'autoprefixer';
import postcssnesting from 'postcss-nesting';

export default {
  plugins: [
    tailwindcss,
    autoprefixer,
    postcssnesting,
  ],
};