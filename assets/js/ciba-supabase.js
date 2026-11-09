// CIBA · Cliente único de autenticación Supabase
// Todos los componentes comparten esta instancia y la misma sesión.
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './ciba-auth-config.js';

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error('Falta la configuración pública de Supabase para CIBA.');
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});
