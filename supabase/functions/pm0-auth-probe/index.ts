import { createClient } from '@supabase/supabase-js';

import { handleOwnerAuthorizationProbe } from '../_shared/owner-authorization.ts';

Deno.serve((request) => {
  return handleOwnerAuthorizationProbe(request, (authorization) => ({
    async evaluate() {
      const supabaseUrl = Deno.env.get('SUPABASE_URL');
      const publishableKey = Deno.env.get('SUPABASE_ANON_KEY');

      if (!supabaseUrl || !publishableKey) {
        return { active: false, error: true };
      }

      const caller = createClient(supabaseUrl, publishableKey, {
        auth: {
          autoRefreshToken: false,
          detectSessionInUrl: false,
          persistSession: false,
        },
        global: {
          headers: { Authorization: authorization },
        },
      });

      const { data, error } = await caller.rpc(
        'pm0_is_active_firebase_owner',
      );

      return {
        active: data === true,
        error: error !== null,
      };
    },
  }));
});
