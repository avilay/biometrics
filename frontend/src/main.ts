import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { Quasar, Dark, Notify, Dialog } from 'quasar';
import router from './router';
import App from './App.vue';

import '@quasar/extras/material-icons/material-icons.css';
import 'quasar/src/css/index.sass';
import './css/app.sass';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(Quasar, {
  plugins: {
    Dark,
    Notify,
    Dialog,
  },
  config: {
    dark: true,
  },
});

app.mount('#app');
