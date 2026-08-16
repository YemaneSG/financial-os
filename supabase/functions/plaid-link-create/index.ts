import { handleHostedLinkCreate } from '../_shared/plaid-hosted-link.ts';
import { createHostedLinkDependencies } from '../_shared/plaid-runtime.ts';

Deno.serve((request) =>
  handleHostedLinkCreate(request, createHostedLinkDependencies())
);
